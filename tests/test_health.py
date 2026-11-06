# =============================================================================
# tests/test_health.py —— 地基冒烟测试
# =============================================================================
# 【这个测试验什么】
#   不验业务（业务还没写），只验「地基是通的」：
#     ① app 能被导入、路由注册成功
#     ② 统一响应封装正常（success / code / result 结构）
#     ③ traceid 中间件真的在工作（响应头带 X-Trace-Id）
#
#   它的价值：以后任何一次改动把中间件、异常处理器、响应封装改坏，
#   这个测试会第一时间红灯。业务测试再按模块往上加。
# =============================================================================


async def test_health_ok(client):
    """健康检查：200 + 统一响应结构 + payload 正确。"""
    res = await client.get("/health")

    assert res.status_code == 200, "健康检查应该200，实际：%s" % res.status_code

    body = res.json()
    assert body["success"] is True, "统一响应里 success 应为 True"
    assert body["code"] == 200, "统一响应里 code 应为 200"
    assert body["result"]["status"] == "healthy", "payload 不对：%s" % body.get("result")


async def test_health_carries_trace_id(client):
    """响应头必须带 X-Trace-Id —— 证明 traceid 中间件真的挂上了。"""
    res = await client.get("/health")

    trace_id = res.headers.get("x-trace-id")
    assert trace_id, "响应头缺少 X-Trace-Id，中间件可能没生效"
    assert len(trace_id) >= 16, "traceid 太短，像是占位值：%s" % trace_id
