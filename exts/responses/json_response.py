# =============================================================================
# exts/responses/json_response.py —— 统一响应格式 + 自定义 JSON 编码器
# =============================================================================
# 【它在链路里的位置】
#   所有接口的返回、所有异常处理器的返回，最终都走这里的 Success / Fail。
#   好处：前端拿到的永远是同一种结构，不用每个接口写一套解析。
#
#   接口正常 → 直接 return dict（FastAPI 自己序列化）
#   需要包装 → return Success(result=...)
#   出错了   → exception.py 里 return Fail(...)
#
# 【统一后的响应长这样】
#   {
#     "success": true,
#     "code": 200,          ← HTTP 状态码
#     "api_code": 200,      ← 业务状态码
#     "message": "Success",
#     "result": {...},      ← 真正的数据
#     "timestamp": 1730000000000
#   }
# =============================================================================

import datetime
import decimal
from pydantic import BaseModel
import json
import time
import typing
from typing import Any, Optional, Dict
from fastapi.responses import JSONResponse
from sqlalchemy.orm import DeclarativeMeta


# -----------------------------------------------------------------------------
# 一、CJsonEncoder —— 解决"这个对象不能直接转 JSON"的问题
# -----------------------------------------------------------------------------
# 【为什么必须自己写一个】
#   json.dumps() 只认 dict / list / str / int / float / bool / None。
#   而数据库查出来的东西里经常有：
#      datetime   → 时间对象，不能直接序列化
#      Decimal    → 金额（数据库 DECIMAL 字段），也不能
#      bytes      → 二进制
#      模型对象   → Doctorinfo 实例，更不行
#   不处理的话，一返回就报 TypeError: Object of type datetime is not JSON serializable
#
# 【怎么工作】
#   json.dumps(..., cls=CJsonEncoder) 遇到不认识的类型时，会调 default() 问一句
#   "这个你打算怎么转？"，我们在这里逐个给出转换规则。
# -----------------------------------------------------------------------------
class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        # ① 支持下标和 keys 的（比如某些 Mapping 类型）→ 直接转 dict
        if hasattr(obj, 'keys') and hasattr(obj, '__getitem__'):
            return dict(obj)
        # ② datetime → '2026-10-28 21:38:44'
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        # ③ date → '2026-10-28'
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        # ④ time → '21:38:44'
        elif isinstance(obj, datetime.time):
            return obj.isoformat()
        # ⑤ Decimal（金额）→ float。★ 注意会丢精度（钱建议转字符串）
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        # ⑥ bytes → utf-8 字符串
        elif isinstance(obj, bytes):
            return str(obj, encoding='utf-8')
        # ⑥.5 【新增】Pydantic 模型（就是我们 schemas 里定义的那些）→ model_dump() 转 dict
        #    ★ 没有这个分支的话，Success(result=DoctorOut(...)) 会报
        #      TypeError: Object of type DoctorOut is not JSON serializable
        #    ★ 为什么要再走一遍 self.default：
        #      model_dump() 出来的 dict 里，Decimal / datetime 还是原对象，
        #      需要再过一遍才会被转成 float / 字符串字符串
        elif isinstance(obj, BaseModel):
            return self.default(obj.model_dump())
        # ⑦ SQLAlchemy 模型对象 → 用 __table__.columns 把每个字段取出来转 dict
        #    （DeclarativeMeta 是所有 ORM 模型类的元类，相当于"这是不是个表模型"）
        elif isinstance(obj.__class__, DeclarativeMeta):
            return self.default({i.name: getattr(obj, i.name) for i in obj.__table__.columns})
        # ⑧ 普通 dict → 逐个值检查，日期/金额继续转，其他一律转字符串
        elif isinstance(obj, dict):
            for k in obj:
                try:
                    if isinstance(obj[k], (datetime.datetime, datetime.date, datetime.time,
                                           decimal.Decimal, bytes)):
                        obj[k] = self.default(obj[k])
                    else:
                        obj[k] = str(obj[k])
                except TypeError:
                    obj[k] = None
            return obj
        # ⑨ 实在不认识，交回父类（父类会抛 TypeError，这是对的，别静默吞掉）
        return json.JSONEncoder.default(self, obj)


# -----------------------------------------------------------------------------
# 二、ApiResponse —— 所有响应类的父类
# -----------------------------------------------------------------------------
# 继承 JSONResponse，所以它本身就是一个可以直接 return 的响应对象。
# 类属性是"默认值"，__init__ 里凡是传了参的就覆盖默认值。
class ApiResponse(JSONResponse):
    http_status_code = 200          # HTTP 状态码
    api_code = 0                    # 业务状态码
    result: Optional[Dict[str, Any]] = None
    message = "Success"
    success = True

    def __init__(self, success=None, http_status_code=None, api_code=None,
                 result=None, message=None, **options):
        # 这一串 "x if x is not None else 默认值" 的写法：
        #   为了区分"没传参（None）"和"传了 0/False 这种假值"。
        #   直接写 self.message = message or self.message 的话，传 "" 会被当成没传。
        self.message = message if message is not None else self.message
        self.api_code = api_code if api_code is not None else self.api_code
        self.success = success if success is not None else self.success
        self.http_status_code = http_status_code if http_status_code is not None else self.http_status_code
        self.result = result if result is not None else self.result

        # 时间戳（毫秒），前端有时需要用来判断数据新旧
        self.timestamp = int(time.time() * 1000)

        body = dict(
            message=self.message,
            code=self.http_status_code,
            success=self.success,
            result=self.result,
            timestamp=self.timestamp,
            api_code=self.api_code
        )
        # 交给父类 JSONResponse 真正构造响应
        super(ApiResponse, self).__init__(status_code=self.http_status_code, content=body, **options)

    def render(self, content: typing.Any) -> bytes:
        """把 dict 转成最终返回给浏览器的字节流。重写它才能用上上面的 CJsonEncoder。"""
        return json.dumps(
            content,
            ensure_ascii=False,          # 中文原样输出，不转 \uXXXX
            allow_nan=False,             # 禁止 NaN/Infinity（不是合法 JSON）
            indent=None,                 # 不美化，省流量
            separators=(',', ':'),       # 紧凑分隔符，再省一点
            cls=CJsonEncoder,            # ★ 关键：用我们自己写的编码器
        ).encode('utf-8')


# -----------------------------------------------------------------------------
# 三、两个成品：成功 / 失败
# -----------------------------------------------------------------------------
class Success(ApiResponse):
    api_code = 0000          # ← 这行的 0000 会被下面那行覆盖（见下方说明）
    http_status_code = 200
    api_code = 200           # ← 真正生效的是这个（Python 后面覆盖前面）
    result = None
    message = "Success"
    success = True
    # ★ 上面 api_code 写了两遍：先 0000 后 200，最终 api_code=200。
    #   这多半是抄代码时的残留。如果原意是"成功码为 0"，应该删掉第二行。
    #   现在不影响运行，但容易让人误读。


class Fail(ApiResponse):
    http_status_code = 200    # 默认 HTTP 200（业务失败也是 200，见 exception.py 的说明）
    api_code = 1000           # 业务错误码，实际调用时会被 exception.py 传的值覆盖
    result = None
    message = "Fail"
    success = False