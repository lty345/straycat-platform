# =============================================================================
# exts/requestvar/__init__.py —— 那块"黑板"的定义（全局唯一）
# =============================================================================
# 【这个文件为什么只有 5 行，却最重要】
#   它是整条日志链路里唯一存放 request_var 的地方。
#   所有需要"当前请求是谁"的代码，都必须从这里 import，不能自己再 new 一个。
#
# 【ContextVar 到底是什么】
#   普通全局变量是全进程共享的（A 请求写进去，B 请求会看到 A 的值 → 串号）。
#   ContextVar 是"按执行上下文隔离"的全局变量：
#     每个请求在 async 世界里跑在各自的上下文里，
#     同一份 ContextVar 在不同上下文里可以存不同的值，互不干扰。
#   这正是我们需要的：几十个请求同时跑，各自都能取到自己那个 request。
#
# 【典型用法】
#   request_var.set(req)   → 存（在中间件里做）
#   request_var.get()      → 取，没存过会抛 LookupError
#   request_var.get(None)  → 取，没存过返回 None（日志函数里用的就是这个，安全）
#   request_var.reset(tok) → 擦（必须在 finally 里做，否则上下文复用时会串号）
#
# 【★ 绝对不要做的三件事】
#   ① 在别的文件里再写一次 ContextVar("request")
#      → 名字一样但不是同一个对象！会造出第二块黑板，读写错开，日志全丢且不报错。
#   ② 忘了 reset
#      → 并发下日志会带着别人的 traceid。
#   ③ 在同步线程池里直接用它
#      → 线程和 async 上下文不共享，会取不到值。
# =============================================================================

from contextvars import ContextVar
from fastapi import Request
from exts.requestvar.bind import bind_contextvar

# 黑板本体。类型标注写成 ContextVar[Request] 只是给 IDE 看的，运行时不做检查。
request_var: ContextVar[Request] = ContextVar("request")

# request 是一个"代理对象"：它本身不是 Request，但它的所有属性访问
# 都会转发到"当前上下文的那个真实 request"上。
#   request.headers  →  实际执行 request_var.get().headers
# 好处：业务代码里可以像用真对象一样用它；缺点是 IDE 不会提示"当前没有 request"。
# 具体原理见 bind.py 的 bind_contextvar()。
request: Request = bind_contextvar(request_var)

# __all__：限制 from exts.requestvar import * 时只导出这两个名字
__all__ = ("request_var", "request")