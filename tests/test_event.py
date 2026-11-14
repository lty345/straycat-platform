# =============================================================================
# tests/test_event.py —— 埋点模块的接口测试
# =============================================================================
# 【和 test_content.py 的区别】
#   content 测的是"读"（分页/排序/详情）；这里测的是"写 + 读回来"，
#   重点是 **list 和 count 的口径一致** —— 这是唯一"不报错但结果错"的 bug 类型。
#
# 【三个测试的分工（少而准）】
#   ① roundtrip     写入能查回来，可选字段落库正确
#   ② total 一致    翻页拿到的条数 == total，无重复无遗漏  ← 最关键
#   ③ 非法枚举      框架层拦截（Literal），业务层不用写判断
# =============================================================================

from datetime import datetime, timedelta

import pytest_asyncio
from sqlalchemy import delete

from db.database import AsyncSessionLocal
from db.model import UserEvent

TEST_USER_ID = 9999
API = "/api/v1/events"
LIST_API = f"/api/v1/users/{TEST_USER_ID}/events"


async def _cleanup():
    """删掉本文件造的所有测试数据。任何测试结束时都该调用它。"""
    async with AsyncSessionLocal() as db:
        await db.execute(delete(UserEvent).where(UserEvent.user_id == TEST_USER_ID))
        await db.commit()


@pytest_asyncio.fixture
async def seeded_events():
    """插 5 条埋点（4 view + 1 like），yield 出 id 列表，结束时删干净。"""
    now = datetime.now()
    rows = [
        UserEvent(
            user_id=TEST_USER_ID,
            target_type="content",
            target_id=100 + i,
            event="view",
            duration_ms=1000 + i,
            create_time=now - timedelta(minutes=5 * i),
        )
        for i in range(4)
    ]
    rows.append(
        UserEvent(
            user_id=TEST_USER_ID,
            target_type="cat",
            target_id=200,
            event="like",
            create_time=now - timedelta(minutes=30),
        )
    )

    async with AsyncSessionLocal() as db:
        db.add_all(rows)
        await db.commit()
        ids = [r.id for r in rows]

    try:
        yield ids
    finally:
        await _cleanup()


# =============================================================================
# ① 写入 → 查回来
# =============================================================================
async def test_create_then_list_roundtrip(client):
    """写入能查回来，且 duration_ms 可以不传（落库为 NULL）。"""
    try:
        # 一条 view，带停留时长
        r1 = await client.post(
            API,
            json={
                "user_id": TEST_USER_ID,
                "target_type": "content",
                "target_id": 555,
                "event": "view",
                "duration_ms": 3000,
            },
        )
        assert r1.status_code == 200, f"写 view 应该 200，实际 {r1.status_code}"
        view_id = r1.json()["result"]["id"]
        assert isinstance(view_id, int) and view_id > 0, f"返回的 id 不合法：{view_id}"

        # 一条 like，故意不传 duration_ms
        r2 = await client.post(
            API,
            json={
                "user_id": TEST_USER_ID,
                "target_type": "cat",
                "target_id": 777,
                "event": "like",
            },
        )
        assert r2.status_code == 200, f"写 like 应该 200，实际 {r2.status_code}"

        # 查回来
        r3 = await client.get(LIST_API)
        assert r3.status_code == 200
        result = r3.json()["result"]
        items = result["list"]

        assert result["total"] == 2, f"应该有 2 条，total 却是 {result['total']}"
        assert len(items) == 2, f"列表长度应该 2，实际 {len(items)}"

        # like 那条的 duration_ms 必须是 None（不传就该是 NULL）
        like_item = next(x for x in items if x["event"] == "like")
        assert like_item["duration_ms"] is None, (
            f"like 没传 duration_ms，应该落库为 None，实际 {like_item['duration_ms']}"
        )

        # view 那条要带着 3000
        view_item = next(x for x in items if x["event"] == "view")
        assert view_item["duration_ms"] == 3000
    finally:
        await _cleanup()


# =============================================================================
# ② total 与翻页一致（★ 最重要的一个）
# =============================================================================
async def test_list_total_matches_across_pages(client, seeded_events):
    """total 必须等于"翻完所有页实际能拿到的条数"。

    这条守的就是你踩过的那个坑：list 和 count 用了不同的 where，
    结果 total=5 但每一页都是空。
    """
    page_size = 2
    collected_ids = []

    for page in (1, 2, 3):
        r = await client.get(f"{LIST_API}?page={page}&page_size={page_size}")
        assert r.status_code == 200
        result = r.json()["result"]

        assert result["total"] == 5, (
            f"第 {page} 页的 total 应该是 5（总条数），实际 {result['total']}"
        )
        collected_ids.extend(x["id"] for x in result["list"])

    # 5 条数据、每页 2 条 → 第 1 页 2 条、第 2 页 2 条、第 3 页 1 条
    assert len(collected_ids) == 5, (
        f"三页合计应该有 5 条，实际 {len(collected_ids)}（可能是重复或遗漏）"
    )
    assert len(set(collected_ids)) == 5, (
        f"翻页出现了重复 id：{collected_ids}（排序不稳定）"
    )


# =============================================================================
# ③ 非法枚举值
# =============================================================================
async def test_invalid_literal_rejected(client):
    """target_type="dog" 被 Pydantic 的 Literal 挡住，返回 400。"""
    r = await client.post(
        API,
        json={
            "user_id": TEST_USER_ID,
            "target_type": "dog",
            "target_id": 1,
            "event": "view",
        },
    )
    assert r.status_code == 400, f"非法 target_type 应该 400，实际 {r.status_code}"
    assert r.json()["success"] is False
