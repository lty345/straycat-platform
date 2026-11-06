# =============================================================================
# exts/requestvar/bind.py —— 两块内容：代理对象 + 写日志的函数
# =============================================================================
# 【它在链路里的位置】
#   ① bind_contextvar()        在 __init__.py 里被调用一次，产出那个 request 代理对象
#   ② async_trace_add_log_record()  在中间件和业务代码里被调用，负责真正写日志
#
#   调用链：中间件 set(request) → 业务/中间件调 ② → ② 去黑板取 traceid → loguru 落盘
# =============================================================================

import json
from typing import Any

from loguru import logger


# -----------------------------------------------------------------------------
# 一、bind_contextvar(黑板) → 返回一个"代理对象"
# -----------------------------------------------------------------------------
# 【为什么要有它】
#   直接从黑板取值要写 request_var.get().headers，又长又丑，还得处处判空。
#   用代理包装后，业务里写 request.headers 就行，看起来像在用一个真 Request。
#
# 【它怎么做到"像真对象"】
#   Python 在访问 obj.xxx 时，如果 obj 上有 __getattr__，就会调它。
#   这里把 6 个魔术方法全部接管，统统转发给 contextvar.get()（当前上下文的真 request）。
#   —— 相当于一个"传声筒"：别人对代理说的话，全转给黑板上的真身。
#
# 【代价】
#   静态类型检查失效。request: Request 这个标注是骗 IDE 的，
#   它实际是 ContextVarBind 实例。所以"当前没有 request"这种错误，
#   IDE 不会报，只能在运行时暴露（这就是之前那个 request 恒为 None 的 bug 藏了那么久的原因）。
# -----------------------------------------------------------------------------
def bind_contextvar(contextvar):
    class ContextVarBind:
        # __slots__=() 表示这个类的实例不存任何自己的属性（没有 __dict__）。
        # 因为它本来就不该存东西 —— 所有数据都在黑板上。
        __slots__ = ()

        # 读属性：proxy.headers → 转发给 真request.headers
        def __getattr__(self, name):
            return getattr(contextvar.get(), name)

        # 写属性：proxy.xxx = v → 写到 真request 上
        def __setattr__(self, name: str, value: Any, /) -> None:
            setattr(contextvar.get(), name, value)

        # 删属性
        def __delattr__(self, name: str, /) -> None:
            delattr(contextvar.get(), name)

        # 下标读：proxy["k"] → 真request["k"]（很少用，但保持接口完整）
        def __getitem__(self, index):
            return contextvar.get()[index]

        # 下标写
        def __setitem__(self, index, value):
            contextvar.get()[index] = value

        # 下标删
        def __delitem__(self, index):
            del contextvar.get()[index]

    # ★ 这一行必须在 class 外面、函数体最后（缩进 4 格）。
    #   之前它被误写进 __delitem__ 里，导致整个函数返回 None，
    #   于是 request 恒为 None，任何 request.xxx 都会 AttributeError。
    return ContextVarBind()


# -----------------------------------------------------------------------------
# 二、async_trace_add_log_record(...) —— 统一的日志写入口
# -----------------------------------------------------------------------------
# 【为什么不直接用 logger.info】
#   直接写的话，每条日志都得自己拼 traceid、自己算序号，业务代码会很脏。
#   这个函数把"取上下文 + 组装字段 + 兜底"三件事封在一起，
#   业务里只要 await async_trace_add_log_record("下单", {"order_id": 123}) 就行。
#
# 【参数】
#   event_type : 事件名，比如 "http_request" / "user_login" / "pay_callback"
#   msg        : dict，这条日志要带的业务信息（为空则日志里不出现该字段）
#   remarks    : 备注字符串（为空则不出现）
#   level      : 日志级别，"INFO"（默认）或 "ERROR"
#                ★ 传 "ERROR" 时这条日志会同时进 info 文件和 error 文件；
#                  不传则只进 info 文件。中间件的异常分支传的就是 "ERROR"。
# -----------------------------------------------------------------------------
async def async_trace_add_log_record(event_type='', msg=None, remarks='', level="INFO"):
    '''
    异步添加日志记录
    :param event_type: 日志记录事件描述
    :param msg: 日志记录信息字典
    :param remarks: 日志备注信息
    :return:
    '''
    # 延迟导入：不能写在文件顶部。
    # 因为 __init__.py 要 import 本文件的 bind_contextvar，
    # 本文件若在顶部再 import __init__ 的 request_var 就是循环导入。
    # 放在函数体里 = 等真正调用时才导入，那时包早已初始化完，安全。
    from exts.requestvar import request_var

    # get(None) 而不是 get()：
    #   没存过值时 get() 会抛 LookupError，get(None) 返回 None。
    #   日志函数会在"没有请求上下文"的场景被调用（比如定时任务、脚本里），
    #   那种情况应该安静跳过，不该炸。
    request = request_var.get(None)

    # 两道判断：
    #   ① request 有没有（有没有正在处理的请求）
    #   ② 这个 request 上有没有 traceid（是不是经过了中间件）
    # 任一不满足就什么都不记 —— 这是"优雅降级"，不是 bug。
    if request and hasattr(request.state, 'traceid'):
        # 取序号 +1 再写回：本条日志是本次请求的第几条。
        # 用 getattr(..., 0) 兜底，因为第一次调用时 state 里还没有这个属性，
        # 不兜底会 AttributeError。
        trace_links_index = request.state.trace_links_index = \
            getattr(request.state, 'trace_links_index', 0) + 1

        log = {
            'traceid': request.state.traceid,      # 这次请求的身份证
            'trace_index': trace_links_index,      # 第几条
            'event_type': event_type,
            'msg': msg,
            'remarks': remarks
        }

        # 空字段从日志里剔掉，避免日志出现 "msg": null 这种噪音
        if not remarks:
            log.pop('remarks')
        if not msg:
            log.pop('msg')

        try:
            # ensure_ascii=False → 中文按原样写，不转成 \uXXXX（否则日志没法看）
            log_msg = json.dumps(log, ensure_ascii=False)
            logger.log(level, log_msg)
        except Exception:
            # 兜底：即使拼 JSON 失败，也要留下一条痕迹，至少知道是哪个请求出的问题。
            # （这里也用同一个 level，所以异常时这条兜底日志同样会进 error 文件）
            logger.log(level, getattr(request.state, 'traceid') + ':索引:' +
                        str(getattr(request.state, 'trace_links_index', 0)) + ':日志信息写入异常')