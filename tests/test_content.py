# =============================================================================
# tests/test_content.py —— 内容模块的接口测试
# =============================================================================
# 【为什么自己造数据，不用 scripts/seed_content.py 的 20 条】
#   种子数据一重跑（清空 + 重插）就变，断言里的数字（total=20）会跟着飘。
#   测试要的是"我自己造的、数量确定的、跑完就删掉"的数据。
#
# 【夹具做了三件事】
#   ① 插 3 条 controllable 数据（时间分别是 今天 / 昨天 / 前天）
#   ② yield 出去三条的 id，测试可以用
#   ③ 测完不管成败都把这三条删掉（finally），不会污染你的开发库
#
# 【你已经有的】
#   tests/conftest.py 里的 client：httpx + ASGITransport，不走端口、不启 uvicorn
# =============================================================================

from datetime import datetime, timedelta

import pytest_asyncio
from sqlalchemy import delete

from db.database import AsyncSessionLocal
from db.model import Content

# 给测试数据加个前缀，万一清理失败也能一眼认出来是谁留下的
PREFIX = "_t_"


@pytest_asyncio.fixture
async def seeded():
    """造 3 条测试数据，yield 出它们的 id 列表，结束时删干净。"""
    now = datetime.now()
    rows = [
        Content(
            title=f"{PREFIX}新",
            summary="s1",
            body="b1",
            tags="测试,边界",
            mood="治愈",
            pub_time=now,
        ),
        Content(
            title=f"{PREFIX}中",
            summary="s2",
            body="b2",
            tags="测试",
            mood="科普",
            pub_time=now - timedelta(days=1),
        ),
        Content(
            title=f"{PREFIX}老",
            summary="s3",
            body="b3",
            tags="测试",
            mood="揪心",
            pub_time=now - timedelta(days=2),
        ),
    ]

    async with AsyncSessionLocal() as db:
        db.add_all(rows)
        await db.commit()          # ★ 必须 commit：接口用的是另一个 session，不提交它看不见
        ids = [r.id for r in rows]  # expire_on_commit=False，所以 commit 后属性还能读

    try:
        yield ids
    finally:
        # 不管测试成功还是失败，都要清理
        async with AsyncSessionLocal() as db:
            await db.execute(delete(Content).where(Content.id.in_(ids)))
            await db.commit()


# =============================================================================
# 下面是你要写的断言。每个函数名写清了"测的是什么"，你只需要填里面。
# 提示：res = await client.get(...)；然后看 res.status_code / res.json()
#      统一响应长这样：{ success, code, api_code, message, result, timestamp }
#      列表接口的 result：{ list: [...], total, page, page_size }
# =============================================================================


async def test_list_pagination_boundary(client, seeded):
    """分页边界：page_size 生效；翻到超出范围的页返回空列表，但 total 不变。"""
    # TODO(你)：
    #   1. GET /api/v1/contents?page=1&page_size=2
    #   2. 断言 status_code == 200
    #   3. 断言 result["list"] 的长度是 2（不是 3、也不是全部）
    #   4. 记下 result["total"]
    #   5. 再 GET /api/v1/contents?page=9999&page_size=2
    #   6. 断言这次的 list 是空列表，且 total 和第 4 步一样
    res = await client.get(f"/api/v1/contents?page=1&page_size=2")
    assert res.status_code == 200, "状态码应该 200,实际%d" % res.status_code
    assert len(res.json()["result"]["list"]) == 2, "列表长度应该 2,实际%d" % len(res.json()["result"]["list"])
    total = res.json()["result"]["total"]
    ras = await client.get(f"/api/v1/contents?page=9999&page_size=2")
    assert len(ras.json()["result"]["list"]) == 0, "列表应该为空,实际%d" % len(ras.json()["result"]["list"])
    assert ras.json()["result"]["total"] == total, "total 应该不变,实际%d" % ras.json()["result"]["total"]

async def test_list_item_has_no_body(client, seeded):
    """列表项不许带正文（第 4 步那条 guard 的回归测试）。"""
    # TODO(你)：GET 列表，取 result["list"][0]，断言 "body" not in item
    res = await client.get(f"/api/v1/contents")
    item = res.json()["result"]["list"][0]
    assert "body" not in item, "列表项不应该带正文,实际%s" % str(list(item.keys()))


async def test_list_order_desc(client, seeded):
    """列表按发布时间倒序：取回来的 pub_time 序列必须严格递减。"""
    # TODO(你)：注意后端返回的 pub_time 是字符串 "2026-11-09 21:16:58"
    #   字符串比较在这里恰好也能用（同格式），但更严谨的做法是转成 datetime 再比
    res = await client.get(f"/api/v1/contents")
    times = [item["pub_time"] for item in res.json()["result"]["list"]]
    assert times == sorted(times, reverse=True), "列表应该按 pub_time 倒序,应该%s,实际%s" % (sorted(times, reverse=True), times)


async def test_detail_ok(client, seeded):
    """详情能查到：200、success 为真、正文不为空。"""
    # TODO(你)：用 seeded[0] 这个 id 去 GET /api/v1/contents/{id}
    res = await client.get(f"/api/v1/contents/{seeded[0]}")
    assert res.status_code == 200, "状态码应该 200,实际%d" % res.status_code
    assert res.json()["success"] is True, "success 应该为真,实际%s" % res.json()["success"]
    assert res.json()["result"]["body"] is not None, "正文不应该为空,实际%s" % res.json()["result"]["body"]


async def test_detail_not_found(client, seeded):
    """查不到时的约定：HTTP 200 + success=false + 业务码 30001（★ 不是 HTTP 404）。"""
    # TODO(你)：用一个大到不可能存在的 id（比如 99999999）
    res = await client.get(f"/api/v1/contents/99999999")
    assert res.status_code == 200, "状态码应该 200,实际%d" % res.status_code
    assert res.json()["success"] is False, "success 应该为假,实际%s" % res.json()["success"]
    assert res.json()["api_code"] == 30001, "业务码应该 30001,实际%d" % res.json()["api_code"]


async def test_invalid_page(client, seeded):
    """参数校验：page=0 应该被挡在 400，不能打到数据库。"""
    # TODO(你)：GET /api/v1/contents?page=0，断言 status_code == 400
    res = await client.get(f"/api/v1/contents?page=0")
    assert res.status_code == 400, "状态码应该 400,实际%d" % res.status_code
