# =============================================================================
# tests/test_feed.py —— 推荐流的接口测试
# =============================================================================
# 只测三条"会悄悄坏掉"的行为：
#   ① 兴趣不同 → top1 不同（MVP 的验收标准）
#   ② 冷启动标记正确（无标签无行为才为 True）
#   ③ 用户不存在 → 业务码 10002
#
# 依赖：content 表里要有内容（推荐是给内容打分的）。没有就自动 skip。
# =============================================================================

import pytest_asyncio
from sqlalchemy import delete

from db.database import AsyncSessionLocal
from db.model import AppUser


async def _cleanup(ids):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(AppUser).where(AppUser.id.in_(ids)))
        await db.commit()


@pytest_asyncio.fixture
async def three_users():
    """造三个用户：猫控 / 救助派 / 纯新人（无标签无行为）。"""
    async with AsyncSessionLocal() as db:
        a = AppUser(nickname="_t_猫控", city="广州", interest_tags="橘猫,日常")
        b = AppUser(nickname="_t_救助派", city="深圳", interest_tags="救助,科普")
        c = AppUser(nickname="_t_新人", city="广州", interest_tags=None)
        db.add_all([a, b, c])
        await db.commit()
        ids = (a.id, b.id, c.id)

    try:
        yield ids
    finally:
        await _cleanup(list(ids))


async def test_feed_top_differs_for_different_interests(client, three_users):
    """★ 兴趣不同的两个用户，top1 应该不同，且命中的是各自的兴趣标签。"""
    # 没有内容就无从打分，直接跳过（避免环境问题导致假失败）
    listed = (await client.get("/api/v1/contents?page_size=1")).json()["result"]
    if listed["total"] == 0:
        import pytest

        pytest.skip("content 表为空，先跑 scripts/seed_content.py")

    cat_lover_id, rescuer_id, _ = three_users

    r1 = (await client.get(f"/api/v1/feed?user_id={cat_lover_id}&page_size=5")).json()["result"]
    r2 = (await client.get(f"/api/v1/feed?user_id={rescuer_id}&page_size=5")).json()["result"]

    assert r1["cold_start"] is False
    assert r2["cold_start"] is False

    top1, top2 = r1["list"][0], r2["list"][0]

    # 顺序不同（这是 MVP 的验收标准）
    assert top1["id"] != top2["id"], (
        f"兴趣不同的两个用户 top1 竟然相同（{top1['title']}），推荐没起作用"
    )

    # 且命中的内容应该带各自的兴趣标签
    assert set((top1["tags"] or "").split(",")) & {"橘猫", "日常"}, (
        f"猫控的 top1 是《{top1['title']}》，标签 {top1['tags']}，不含他的兴趣"
    )
    assert set((top2["tags"] or "").split(",")) & {"救助", "科普"}, (
        f"救助派的 top1 是《{top2['title']}》，标签 {top2['tags']}，不含他的兴趣"
    )

    # 分数必须递减（排序生效）
    scores = [x["score"] for x in r1["list"]]
    assert scores == sorted(scores, reverse=True), f"分数没有递减：{scores}"


async def test_feed_cold_start_flag(client, three_users):
    """没标签、没行为的用户 → cold_start 为 True，且 reason 说明是兜底。"""
    _, _, newbie_id = three_users

    result = (await client.get(f"/api/v1/feed?user_id={newbie_id}")).json()["result"]

    assert result["cold_start"] is True, "新用户应该走冷启动兜底"
    assert result["preferred_mood"] is None, "没有行为就算不出情绪偏好"
    if result["list"]:
        assert "冷启动" in result["list"][0]["reason"]


async def test_feed_unknown_user(client):
    """不存在的用户 → 业务码 10002。"""
    res = await client.get("/api/v1/feed?user_id=999999")
    body = res.json()

    assert body["success"] is False
    assert body["api_code"] == 10002, f"应该是 10002（用户不存在），实际 {body['api_code']}"
