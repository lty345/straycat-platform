# =============================================================================
# exts/exceptions/exception.py —— 全局统一异常处理
# =============================================================================
# 【它在链路里的位置】
#   中间件里 raise 出去的异常，最终都由这里接住，转成统一的 JSON 响应。
#
#   请求 → 中间件 → 业务函数抛异常 → 冒泡到 FastAPI
#        → ApiExceptionHandler 里对应的 handler
#        → 返回 Fail(...) 这种统一格式的 JSON
#
# 【为什么要统一】
#   不然 500 报错时前端拿到的是 FastAPI 默认的 HTML 错误页 / 一段丑陋的 traceback，
#   前端没法解析。统一之后，前端永远只需要判断 success 字段。
#
# 【★ 和日志链路的联系（已打通）】
#   中间件里那个 X-Trace-Id 是在 call_next 成功返回后才加的；
#   一旦抛异常，call_next 直接抛出，那行代码执行不到 ——
#   所以「异常响应」不是中间件生成的，而是由本文件这 4 个 handler 生成的。
#
#   结论：谁生成响应，谁负责贴标签。
#   所以下面 4 个 handler 都是同一个套路：
#       ① resp = Fail(...)                                  先造响应（各自的业务逻辑不同）
#       ② tid = getattr(request.state, "traceid", "")        从 request 拿 traceid
#       ③ if tid: resp.headers["X-Trace-Id"] = tid           给刚造的响应加头
#       ④ return resp
#
#   为什么能从 request 拿到：request.state.traceid 是中间件在请求刚进来时就设好的，
#   异常不会把它抹掉。response 对象没了，但 request 还在。
#
# 【★★ 最容易漏的一步：必须注册，否则整个文件是死代码 ★★】
#   光定义这 4 个 handler 不起作用，必须在 app.py 里调用：
#       from exts.exceptions.exception import ApiExceptionHandler
#       ApiExceptionHandler(app)
#   不注册的症状：500 时返回纯文本 "Internal Server Error"（FastAPI 默认），
#                没有统一 JSON 格式，也没有 X-Trace-Id。
# =============================================================================

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from enum import Enum

from exts.responses.json_response import Fail


# -----------------------------------------------------------------------------
# 业务错误码表
# -----------------------------------------------------------------------------
# 用 Enum 的好处：调用处写 ExceptionEnum.USER_NO_DATA，参数写错 IDE 会报，
#   而且能把 (code, 描述) 打包成一对。
# ★ 码段约定见下方 ExceptionEnum 内的注释，别在代码里临场写数字。
#     业务码  → 前端判断"具体什么错"（30001 = 内容不存在）
#     HTTP码 → 网关/监控/浏览器判断"这次请求算不算失败"
#
# ★★ 本项目的实际约定（已定，别再改回去）★★
#   BusinessError 一律返回 HTTP 200 + 业务码，理由：
#     服务器没崩、路由存在、参数也合法 —— 只是业务规则不满足。
#     这样前端只判 success / api_code 一处，不用同时看 HTTP 状态码。
#   具体划分：
#     资源不存在（查不到）      → HTTP 200 + 业务码 3xxxx（如 30001 内容不存在）
#     请求本身有问题（参数错）  → HTTP 400（由 RequestValidationError 统一处理）
#     没登录 / 身份无效        → HTTP 401
#     登录了但没权限           → HTTP 403
#     资源存在但规则不允许     → HTTP 200 + 业务码（号源抢完、已被他人申请）
#     路由不存在（框架级 404） → HTTP 404（见 http_exception_handler）
#   ★ 一句话区分：HTTP 状态码回答"请求有没有到达业务"，
#                 业务码回答"业务有没有成功"。前者多由框架决定，后者由你决定。
class ExceptionEnum(Enum):
    # ---- 通用（每个项目都这几个）----
    SUCCESS = (0, "OK")
    PARAMETER_ERROR = (10001, "参数错误")
    USER_NO_DATA = (10002, "用户不存在")
    PERMISSIONS_ERROR = (10403, "无权限")
    FAILED = (50000, "系统异常")

    # ---- 业务码：按模块分段占号，避免撞号 ----
    # ★ 规矩：每加一个业务错误，先在这里登记，别在代码里临场写数字。
    #   码段约定（照这个扩展）：
    #     10000~19999 通用 / 参数 / 用户
    #     20000~29999 领养（抢占类）
    #     30000~39999 内容
    #     40000~49999 推荐 / 埋点
    ADOPT_TAKEN = (20001, "这只猫已被他人申请")
    ADOPT_DUPLICATE = (20002, "您已提交过申请")

    CONTENT_NOT_FOUND = (30001, "内容不存在")

    EVENT_INVALID = (40001, "埋点事件不合法")


# -----------------------------------------------------------------------------
# 业务异常：主动"抛"出去表达"这个业务走不通了"
# -----------------------------------------------------------------------------
# 和普通 Exception 的区别：
#   普通 Exception 是"程序出 bug 了"（500），
#   BusinessError 是"业务规则不允许"（比如余额不足、重复预约），属于预期内的情况。
# 用法：raise BusinessError(ExceptionEnum.USER_NO_DATA)
#       或者 raise BusinessError(err_code="3001", err_code_des="号源已抢完")
class BusinessError(Exception):
    __slots__ = ['err_code', 'err_code_des']     # 只允许这两个属性，省内存

    def __init__(self, result: ExceptionEnum = None, err_code: str = "0000", err_code_des: str = ""):
        # 两种用法：
        #   BusinessError(ExceptionEnum.XXX)                     → 从枚举里取 code 和描述
        #   BusinessError(err_code="3001", err_code_des="xxx")   → 直接传
        if result:
            self.err_code = result.value[0]
            # 传了自定义描述用自定义的，没传用枚举里的
            self.err_code_des = err_code_des or result.value[1]
        else:
            self.err_code = err_code
            self.err_code_des = err_code_des
        super().__init__(self.err_code, self.err_code_des)


# -----------------------------------------------------------------------------
# handler 注册器：把 4 类异常分别挂到各自的处理函数上
# -----------------------------------------------------------------------------
class ApiExceptionHandler:
    def __init__(self, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if app is not None:
            self.init_app(app)

    def init_app(self, app: FastAPI):
        # 四类异常，四种待遇：
        #   1) Exception                   → 一切没被单独处理的异常（兜底，500）
        #   2) StarletteHTTPException      → 框架自己抛的 404 / 405 等
        #   3) BusinessError               → 我们主动抛的业务异常
        #   4) RequestValidationError      → 请求参数不合法（Pydantic 校验失败）
        app.add_exception_handler(Exception, handler=self.all_exception_handler)
        app.add_exception_handler(StarletteHTTPException, handler=self.http_exception_handler)
        app.add_exception_handler(BusinessError, handler=self.all_businesserror_handler)
        app.add_exception_handler(RequestValidationError, handler=self.validation_exception_handler)

    # ---- ① 参数校验失败（比如该传 int 传了 "abc"）-----------------------------
    async def validation_exception_handler(self, request: Request, exc: RequestValidationError):
        # HTTP 400 + 把 Pydantic 的详细错误和原始请求体一起返回，方便前端定位
        # 参数校验失败：HTTP 400 + Pydantic 的详细信息（哪个字段、什么错、前端传了什么）
        resp = Fail(
            http_status_code=400,
            api_code=400,
            message='参数错误',
            result={
                "detail": exc.errors(),
                "body": exc.body
            }
        )
        tid = getattr(request.state, "traceid", "")
        if tid:
            resp.headers["X-Trace-Id"] = tid
        return resp

    # ---- ② 业务异常 ----------------------------------------------------------
    async def all_businesserror_handler(self, request: Request, exc: BusinessError):
        # ★ 注意 http_status_code=200：业务失败也返回 HTTP 200。
        #   这是国内很多项目的约定 —— 只要服务器没崩，HTTP 就是 200，
        #   真正的成败靠响应体里的 api_code / success 判断。
        #   （另一种流派是 4xx，看你团队约定）
        # 业务异常：HTTP 200 + 业务错误码（成败看 api_code，不看 HTTP 状态码）
        resp = Fail(
            http_status_code=200,
            api_code=exc.err_code,
            message=exc.err_code_des
        )
        tid = getattr(request.state, "traceid", "")
        if tid:
            resp.headers["X-Trace-Id"] = tid
        return resp

    # ---- ③ 兜底：所有没被单独接住的异常（真·程序 bug）------------------------
    async def all_exception_handler(self, request: Request, exc: Exception):
        # 这里只有 500。★ 建议把 exc 的信息也记一笔日志，
        #   否则排查时只知道"系统异常"，不知道具体是什么异常。
        # 兜底异常：真·程序 bug，统一 500
        resp = Fail(http_status_code=500, api_code=5000, message="系统异常")
        tid = getattr(request.state, "traceid", "")
        if tid:
            resp.headers["X-Trace-Id"] = tid
        return resp

    # ---- HTTP 状态码 → 中文描述 ---------------------------------------------
    STATUS_MAP = {
        400: (400, "参数错误"),
        401: (401, "未授权"),
        403: (403, "禁止"),
        404: (404, "未找到"),
        405: (405, "方法不允许"),
        429: (429, "请求过于频繁"),
        500: (500, "服务器错误")
    }

    # ---- ④ 框架级 HTTP 异常（404 找不到路由、405 方法不对等）------------------
    async def http_exception_handler(self, request: Request, exc: StarletteHTTPException):
        # 先在表里查中文描述，查不到就用原始 detail
        # 框架级 HTTP 异常：先查表拿中文描述，查不到就用原始 detail
        http_code, message = self.STATUS_MAP.get(exc.status_code, (exc.status_code, exc.detail or "请求失败"))
        resp = Fail(http_status_code=http_code, api_code=http_code, message=message)
        tid = getattr(request.state, "traceid", "")
        if tid:
            resp.headers["X-Trace-Id"] = tid
        return resp