# =============================================================================
# middlewares/loger/logmiddleware.py —— 日志中间件（整条链路的核心）
# =============================================================================
# 【中间件是什么】
#   它是包在每个请求外面的一层"壳"。请求进来时先过它，业务跑完后再回到它。
#
#       请求 →┌─────────────────────────────┐
#             │  中间件（本文件）            │
#             │  ├ 分配 traceid              │
#             │  ├ 把 request 放上"黑板"     │
#             │  ├ →→ 你的业务函数 →→        │
#             │  ├ 记录耗时 / 状态码         │
#             │  └ 从"黑板"上把 request 拿走 │
#             └─────────────────────────────┘→ 响应
#
# 【为什么需要它】
#   没有中间件时：业务代码想记一条"这次请求干了些啥"的日志，是拿不到
#   request 对象的（难道每个函数都加一个 request 参数？）。
#   有了中间件：请求一进来就把 request 存到"黑板"上，之后任何地方都能取。
#
# 【黑板在哪】
#   exts/requestvar/__init__.py 里的 request_var（一个 ContextVar）。
#   ★ 那个 ContextVar 全局只能有一份！本文件只是"从它那儿 import 过来用"，
#     绝对不能在这里再写一次 ContextVar("request") —— 那会造出第二块黑板，
#     中间件往新黑板写、日志函数从旧黑板读，日志就会全部静默丢失。
# =============================================================================

from fastapi import Request
from time import perf_counter          # 高精度计时器，专门用来算耗时
import uuid                            # 用来生成 traceid
from exts.requestvar import request_var              # ★ 那块"黑板"（全局唯一）
from exts.requestvar.bind import async_trace_add_log_record   # 写日志的函数


def setup_log_middleware(application):
    """
    把日志中间件注册到 app 上。

    为什么包成一个函数，而不是在文件顶部直接写 @app.middleware？
      因为如果写 @app.middleware，这个文件就必须 from app import app，
      而 app.py 又要 import 这个文件 —— 两边互相导入 = 循环导入，启动直接崩。
      现在改成：谁需要谁传进来（app.py 里 setup_log_middleware(app)），
      本文件不依赖任何外部 app，彻底避开循环。
    """

    # @application.middleware("http") 装饰器：
    #   把下面这个函数登记为"每个 HTTP 请求都要经过的一层"
    @application.middleware("http")
    async def log_request(request: Request, call_next):
        # call_next 是"通往下一层"的开关：await 它，请求才会继续往下走到业务函数

        # ---- 第 1 步：给这次请求发一个身份证 ----------------------------------
        # uuid4().hex 生成 32 位十六进制随机串，例如 d30727a41a2c4aba8293622565082d37
        # 同一次请求里产生的所有日志都会带上它 → 出事时靠它把日志串起来
        request.state.traceid = uuid.uuid4().hex

        # trace_links_index = "这是本次请求的第几条日志"，从 0 开始，
        # 每记一条日志 +1（+1 的动作在 bind.py 的日志函数里做）
        request.state.trace_links_index = 0

        # ---- 第 2 步：把 request 放上"黑板" -----------------------------------
        # set() 返回一个 token（凭证），最后必须用它 reset() 把黑板擦掉。
        # 为什么必须擦：黑板是按"执行上下文"隔离的，但上下文会随任务复用；
        # 不擦的话，下一个请求可能读到上一个请求的 request（串号）。
        token = request_var.set(request)

        try:
            # ---- 第 3 步：计时并放行到业务层 ----------------------------------
            t0 = perf_counter()                    # 开始计时
            response = await call_next(request)    # ★ 请求从这里进入业务函数，跑完再回来
            cost_ms = round((perf_counter() - t0) * 1000, 2)   # 换算成毫秒，保留 2 位

            # ---- 第 4 步：记录一条成功的访问日志 ------------------------------
            # 这里没有直接 logger.info，而是调日志函数：
            #   由它去黑板上取 traceid，自动带上 traceid + 递增索引
            await async_trace_add_log_record(
                event_type="http_request",
                msg={"method": request.method, "path": request.url.path,
                     "status_code": response.status_code, "cost_ms": cost_ms},
            )

            # ---- 第 5 步：把 traceid 塞进响应头 --------------------------------
            # 这样前端 / 报障的用户也能拿到 traceid 告诉你，你才能去日志里搜。
            response.headers["X-Trace-id"] = request.state.traceid
            return response

        # ---- 异常分支：业务函数抛异常时走这里 --------------------------------
        except Exception as e:
            # 异常分支记日志的两个要点：
            #   ① remarks 里带上 type(e).__name__ 和 e 的内容
            #      → 日志里直接能看到 "OperationalError: Can't connect to MySQL"，
            #        不用去翻 500 行的 traceback 才知道错在哪
            #   ② level="ERROR"
            #      → 这条日志会同时写进 info 和 error 两个文件
            #        （error_log_file_path 那个 handler 只收 ERROR 及以上）
            await async_trace_add_log_record(
                event_type="http_request",
                msg={"method": request.method, "path": request.url.path},
                remarks=f"请求异常: {type(e).__name__}: {e}",  # ← 顺便把异常内容带上
                level="ERROR",  # ← 加这一行
            )
            raise

            # raise 把异常继续往上抛 → 交给 exts/exceptions/exception.py 统一处理成 500 响应
            # ★ 注意副作用：异常时第 5 步执行不到，所以 500 响应里没有 X-Trace-Id 头。
            #   要补的话得在 exception.py 的 handler 里加。
            raise

        # ---- 无论成功还是异常，最后都要把黑板擦干净 --------------------------
        # finally 保证"就算上面崩了也会执行"
        # reset(token) 只擦掉自己写的那次，不会误伤别的请求的上下文
        finally:
            request_var.reset(token)