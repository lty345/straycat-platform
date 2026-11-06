# =============================================================================
# exts/logururoute/loguru_config.py —— loguru 日志总配置
# =============================================================================
# 【它在链路里的位置】
#   app.py 第一件事就是调它。它只做一件事：
#   把 loguru 从"默认往控制台吐"改造成"控制台 + 两个文件，按天分卷"。
#
# 【改造后一共 3 个出口（sink）】
#   ┌ 控制台 stdout          ：所有级别，带颜色（开发时看）
#   ├ log/info2026xxxx.log   ：INFO 及以上全收（日常排查用）
#   └ log/error2026xxxx.log  ：只收 ERROR 及以上（出事故时直接看这个文件）
#
#   ★ 注意"全收"的含义：ERROR 级别的日志会同时出现在 info 文件和 error 文件里。
#     这是故意的 —— info 记录全过程，error 只挑出错的，两边都能查到。
#
# 【关键概念】
#   rotation="00:00"  每天零点换一个新文件，文件名里的 {time:YYYYMMDD} 会重新渲染
#   level="INFO"      只接收 INFO 及以上（DEBUG 会被丢掉）
#   enqueue=True      日志先入内存队列，由后台线程落盘 → 不阻塞业务
#                     （代价：程序如果瞬间退出，队列里的日志可能丢，
#                       关闭服务时最好调一下 logger.complete()）
# =============================================================================

from loguru import logger


def setup_ext_loguru(log_pro_path: str = None):
    """
    初始化日志系统。传了 log_pro_path 就用它当日志目录，不传就自动推。

    ★ 必须在 app = FastAPI(...) 之前调用：
      它内部的 logger.configure(handlers=[...]) 会清空 loguru 原有的 handler，
      如果放在 app 创建之后调，FastAPI 启动阶段产生的日志就被清掉了。
    """
    import os

    # ---- 算出日志目录 --------------------------------------------------------
    # 这段是"往上找项目根，再进 log 目录"：
    #   本文件路径 = 项目根/exts/logururoute/loguru_config.py
    #     dirname ①  → 项目根/exts/logururoute
    #     dirname ②  → 项目根/exts
    #     dirname ③  → 项目根           ← 到这里
    #   再拼上 "log" → 项目根/log
    #
    # ★ 为什么不用 os.path.split(__file__)[0]（自己所在目录）？
    #   那样的话，这个文件被挪到哪个目录，日志就写到哪个目录。
    #   之前从 log/ 挪到 exts/logururoute/ 时，日志就跟着跑进了代码目录里。
    #   锚定"项目根"才稳定，以后随便挪文件日志都不会乱跑。
    if not log_pro_path:
        log_pro_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "log",
        )

    # {time:YYYYMMDD} 是 loguru 的占位符，每天生成新文件名时会被替换成 20261028
    log_file_path = os.path.join(log_pro_path, "info{time:YYYYMMDD}.log")
    error_log_file_path = os.path.join(log_pro_path, "error{time:YYYYMMDD}.log")

    from sys import stdout

    # ---- 出口 1：控制台 ------------------------------------------------------
    # 带 <green> 这类标签是 loguru 的颜色标记，只在控制台生效，写文件时不能用。
    LOGURU_FORMAT: str = ('<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | '
                          '<level>{level: <16}</level> | <bold> {message} </bold>')
    # configure(handlers=[...]) = "清空现有全部 handler，只保留这一个"
    # loguru 默认自带一个 stderr handler，不清掉的话每条日志会打印两遍
    logger.configure(handlers=[{'sink': stdout, 'format': LOGURU_FORMAT}])

    # ---- 出口 2：info 文件（收 INFO 及以上）-----------------------------------
    # 格式字段说明（这里踩过坑，字段名写错会导致日志一条都写不进去且不报错）：
    #   {time}         时间
    #   {process}      进程 ID      （不是 process_id！）
    #   {process.name} 进程名
    #   {thread}       线程 ID      （不是 thread_id！）
    #   {thread.name}  线程名       （不是 thread_name！）
    #   {level}        级别
    #   {message}      日志内容
    # 这里的 "|\n {message}" 让内容换到下一行 —— 好处是长 JSON 好读，
    # 坏处是每条日志占两行，以后用脚本按行统计时要记得这点。
    format = ("{time:YYYY-MM-DD  HH:mm:ss:SSS}  | pid:{process} {process.name} | "
              "tid:{thread} {thread.name} | {level} |\n {message}")
    logger.add(log_file_path, format=format, rotation="00:00",
               encoding="utf-8", level="INFO", enqueue=True)

    # ---- 出口 3：error 文件（只收 ERROR 及以上）------------------------------
    # 注意 level="ERROR"：普通 INFO 日志进不来，只有 ERROR 及以上才会写进这里。
    #
    # 【这个文件现在是真有用的】
    #   bind.py 的日志函数已经支持 level 参数：
    #     正常请求  → 不传 level（默认 INFO）→ 只进 info 文件
    #     发生异常  → 中间件传 level="ERROR"  → 同时进 info 和 error 两个文件
    #   所以 error 文件里只有出问题的请求，出事故时直接看这一个文件就够了。
    #
    # ★ 注意 level="ERROR" 不是"只收 ERROR"而是"收 ERROR 及以上"（ERROR、CRITICAL）。
    #   另外 loguru 的级别顺序是：TRACE < DEBUG < INFO < SUCCESS < WARNING < ERROR < CRITICAL
    format2 = ("{time:YYYY-MM-DD  HH:mm:ss:SSS}  | pid:{process} {process.name} | "
               "tid:{thread} {thread.name} | {level} | {message}")
    logger.add(error_log_file_path, format=format2, rotation="00:00",
               encoding="utf-8", level="ERROR", enqueue=True)