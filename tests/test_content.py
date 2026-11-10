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
    res = await client.get("/api/v1/contents?page=1&page_size=2")
    assert res.status_code == 200, "状态码应该 200,实际%d" % res.status_code
    first_page = res.json()["result"]
    assert len(first_page["list"]) == 2, "列表长度应该 2,实际%d" % len(first_page["list"])
    total = first_page["total"]

    res2 = await client.get("/api/v1/contents?page=9999&page_size=2")
    assert res2.status_code == 200, "越界页不该报错,实际%d" % res2.status_code
    second_page = res2.json()["result"]
    assert len(second_page["list"]) == 0, "越界页列表应该为空,实际%d" % len(second_page["list"])
    assert second_page["total"] == total, "越界页 total 应该不变,实际%d,期望%d" % (second_page["total"], total)


async def test_list_item_has_no_body(client, seeded):
    """列表项不许带正文（ContentListOut / ContentDetailOut 拆分的回归防线）。"""
    res = await client.get("/api/v1/contents")
    items = res.json()["result"]["list"]
    assert items, "夹具没造出数据，后面的断言无从谈起"
    item = items[0]
    assert "body" not in item, "列表项不应该带正文,实际有这些键:%s" % str(list(item.keys()))


async def test_list_order_desc(client, seeded):
    """列表按发布时间倒序：取回来的 pub_time 序列必须严格递减。"""
    res = await client.get("/api/v1/contents")
    times = [item["pub_time"] for item in res.json()["result"]["list"]]

    # ★ pub_time 允许为 NULL。null 混进来时 sorted() 会抛 TypeError，
    #   那时的报错完全不指向真实原因，所以先把"有没有 null"单独断言出来。
    nulls = [i for i, t in enumerate(times) if t is None]
    assert not nulls, "列表里有 pub_time 为 NULL 的记录，下标:%s（表允许可空，但排序断言需要它们有值）" % nulls

    assert times == sorted(times, reverse=True), "列表应该按 pub_time 倒序,应该%s,实际%s" % (
        sorted(times, reverse=True),
        times,
    )


async def test_detail_ok(client, seeded):
    """详情能查到：200、success 为真、正文不为空。"""
    res = await client.get(f"/api/v1/contents/{seeded[0]}")
    assert res.status_code == 200, "状态码应该 200,实际%d" % res.status_code
    assert res.json()["success"] is True, "success 应该为真,实际%s" % res.json()["success"]
    assert res.json()["result"]["body"] is not None, "正文不应该为空,实际%s" % res.json()["result"]["body"]


async def test_detail_not_found(client, seeded):
    """查不到时的约定：HTTP 200 + success=false + 业务码 30001（★ 不是 HTTP 404）。"""
    res = await client.get("/api/v1/contents/99999999")
    assert res.status_code == 200, "状态码应该 200,实际%d" % res.status_code
    assert res.json()["success"] is False, "success 应该为假,实际%s" % res.json()["success"]
    assert res.json()["api_code"] == 30001, "业务码应该 30001,实际%d" % res.json()["api_code"]


async def test_invalid_page(client, seeded):
    """参数校验：page=0 应该被挡在 400，不能打到数据库。"""
    res = await client.get("/api/v1/contents?page=0")
    assert res.status_code == 400, "状态码应该 400,实际%d" % res.status_code
