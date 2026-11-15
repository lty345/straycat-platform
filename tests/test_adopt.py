# =============================================================================
# tests/test_adopt.py —— 领养抢占的接口测试
# =============================================================================
# 核心是最后一条：并发 10 个请求抢同一只猫，只能成功 1 个。
# 这条测试守的是"检查和修改没压进同一条 UPDATE"这类竞态 bug——
# 用 SELECT-then-UPDATE 写法时它会红，用原子 UPDATE 时它绿。
# =============================================================================

import asyncio

import pytest_asyncio
from sqlalchemy import delete, select

from db.database import AsyncSessionLocal
from db.model import Cat


async def _cleanup(ids):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Cat).where(Cat.id.in_(ids)))
        await db.commit()


@pytest_asyncio.fixture
async def two_cats():
    """一只待领养、一只已领养。"""
    async with AsyncSessionLocal() as db:
        adoptable = Cat(name="_t_待领养", breed="橘猫", city="广州", status="待领养")
        taken = Cat(name="_t_已领养", breed="黑猫", city="广州", status="已领养", applicant_id=1)
        db.add_all([adoptable, taken])
        await db.commit()
        ids = (adoptable.id, taken.id)

    try:
        yield ids
    finally:
        await _cleanup(list(ids))


async def _get_cat(cat_id):
    """从数据库直接读状态，避免只信接口返回。"""
    async with AsyncSessionLocal() as db:
        return (
            await db.execute(select(Cat).where(Cat.id == cat_id))
        ).scalar_one()


async def test_adopt_ok(client, two_cats):
    """抢一只待领养的猫：200，且数据库里状态和申请人真的变了。"""
    adoptable_id, _ = two_cats

    res = await client.post(f"/api/v1/cats/{adoptable_id}/adopt", json={"user_id": 42})
    assert res.status_code == 200, res.text
    assert res.json()["success"] is True

    cat = await _get_cat(adoptable_id)
    assert cat.status == "审核中", f"状态应变成「审核中」，实际「{cat.status}」"
    assert cat.applicant_id == 42, f"申请人应写入 42，实际 {cat.applicant_id}"


async def test_adopt_twice_rejected(client, two_cats):
    """同一只猫第二次申请 → 20001。"""
    adoptable_id, _ = two_cats

    first = await client.post(f"/api/v1/cats/{adoptable_id}/adopt", json={"user_id": 1})
    assert first.json()["success"] is True

    second = await client.post(f"/api/v1/cats/{adoptable_id}/adopt", json={"user_id": 2})
    body = second.json()
    assert body["success"] is False
    assert body["api_code"] == 20001, f"应该是 20001，实际 {body['api_code']}"

    cat = await _get_cat(adoptable_id)
    assert cat.applicant_id == 1, "第一个申请人不能被覆盖"


async def test_adopt_already_adopted_rejected(client, two_cats):
    """抢一只已领养的猫 → 20001。"""
    _, taken_id = two_cats

    res = await client.post(f"/api/v1/cats/{taken_id}/adopt", json={"user_id": 7})
    body = res.json()
    assert body["success"] is False
    assert body["api_code"] == 20001


async def test_adopt_concurrent_only_one_wins(client):
    """★ 并发 10 个请求抢同一只猫：恰好 1 个成功，数据库里只有一个申请人。

    这是"一只猫只能被一人申请"的唯一可信验证方式。
    串行地测两次申请，看不出竞态；并发才看得出。
    """
    async with AsyncSessionLocal() as db:
        cat = Cat(name="_t_并发", breed="狸花", city="深圳", status="待领养")
        db.add(cat)
        await db.commit()
        cat_id = cat.id

    try:
        async def hit(uid):
            resp = await client.post(f"/api/v1/cats/{cat_id}/adopt", json={"user_id": uid})
            return resp.json().get("api_code")

        codes = await asyncio.gather(*[hit(100 + i) for i in range(10)])

        successes = [c for c in codes if c == 200]
        rejected = [c for c in codes if c == 20001]

        assert len(successes) == 1, (
            f"并发 10 个应该只有 1 个成功，实际成功 {len(successes)} 个：{codes}"
        )
        assert len(rejected) == 9, f"应该有 9 个被拒，实际 {len(rejected)} 个：{codes}"

        cat = await _get_cat(cat_id)
        assert cat.status == "审核中"
        assert cat.applicant_id in range(100, 110), "申请人必须是那 10 个之一"
    finally:
        await _cleanup([cat_id])
