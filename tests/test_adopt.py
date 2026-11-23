# =============================================================================
# tests/test_adopt.py —— 领养抢占的接口测试
# =============================================================================
# 核心是最后一条：并发 10 个请求抢同一只猫，只能成功 1 个。
# 这条测试守的是"检查和修改没压进同一条 UPDATE"这类竞态 bug——
# 用 SELECT-then-UPDATE 写法时它会红，用原子 UPDATE 时它绿。
#
# ★ 加入登录之后，测试要造"真用户 + 真 token"：
#   以前请求体里塞 user_id 就行，但那个 id 是假的，测不出"谁抢到了"。
# =============================================================================

import asyncio
import uuid

import bcrypt
import pytest_asyncio
from sqlalchemy import delete, select

from db.database import AsyncSessionLocal
from db.model import AppUser, Cat
from exts.security import create_access_token

# 测试专用哈希：rounds=4（约 2ms）而不是线上的 12（约 250ms），
# 否则光建 10 个用户就要 2.5 秒，测试会慢得没人想跑
_TEST_HASH = bcrypt.hashpw(b"test12345", bcrypt.gensalt(rounds=4)).decode()


async def _make_users(n: int) -> list[int]:
    """批量建测试用户，返回 id 列表。"""
    async with AsyncSessionLocal() as db:
        users = [
            AppUser(username=f"_t_u{i}_{uuid.uuid4().hex[:6]}", password_hash=_TEST_HASH)
            for i in range(n)
        ]
        db.add_all(users)
        await db.commit()
        return [u.id for u in users]


def _headers(user_id: int) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


async def _cleanup(cat_ids, user_ids=()):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Cat).where(Cat.id.in_(cat_ids)))
        if user_ids:
            await db.execute(delete(AppUser).where(AppUser.id.in_(user_ids)))
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


@pytest_asyncio.fixture
async def three_users():
    """三个可登录的测试用户。"""
    ids = await _make_users(3)
    try:
        yield ids
    finally:
        await _cleanup([], ids)


async def _get_cat(cat_id):
    """从数据库直接读状态，避免只信接口返回。"""
    async with AsyncSessionLocal() as db:
        return (
            await db.execute(select(Cat).where(Cat.id == cat_id))
        ).scalar_one()


async def _wait_cat(cat_id, predicate, timeout: float = 2.0):
    """等到猫的状态满足条件。

    ★ 为什么需要它：FastAPI 的 yield 依赖在**响应发出之后**才执行 commit，
      所以 POST 返回 200 后立刻查库，偶尔会读到提交前的旧数据。
      用户无感，但测试会偶发失败 —— 用"轮询到成立为止"消除这个竞态。
    """
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    cat = await _get_cat(cat_id)
    while loop.time() < deadline:
        if predicate(cat):
            return cat
        await asyncio.sleep(0.05)
        cat = await _get_cat(cat_id)
    return cat


async def test_adopt_requires_login(client, two_cats):
    """★ 新增：不带 token 不能申请，而且猫的状态不能被改动。"""
    adoptable_id, _ = two_cats

    res = await client.post(f"/api/v1/cats/{adoptable_id}/adopt")
    body = res.json()
    assert body["success"] is False
    assert body["api_code"] == 10401, f"未登录应返回 10401，实际 {body['api_code']}"

    cat = await _get_cat(adoptable_id)
    assert cat.status == "待领养", "未登录的请求不能改变猫的状态"
    assert cat.applicant_id is None


async def test_adopt_ok(client, two_cats, three_users):
    """抢一只待领养的猫：200，且数据库里状态和申请人真的变了。"""
    adoptable_id, _ = two_cats
    alice = three_users[0]

    res = await client.post(
        f"/api/v1/cats/{adoptable_id}/adopt", headers=_headers(alice)
    )
    assert res.status_code == 200, res.text
    assert res.json()["success"] is True

    cat = await _wait_cat(adoptable_id, lambda c: c.status == "审核中")
    assert cat.status == "审核中", f"状态应变成「审核中」，实际「{cat.status}」"
    assert cat.applicant_id == alice, f"申请人应是 {alice}，实际 {cat.applicant_id}"


async def test_adopt_twice_rejected(client, two_cats, three_users):
    """同一只猫：A 申请后 B 再申请 → 20001，申请人仍是 A。"""
    adoptable_id, _ = two_cats
    alice, bob = three_users[0], three_users[1]

    first = await client.post(
        f"/api/v1/cats/{adoptable_id}/adopt", headers=_headers(alice)
    )
    assert first.json()["success"] is True

    second = await client.post(
        f"/api/v1/cats/{adoptable_id}/adopt", headers=_headers(bob)
    )
    body = second.json()
    assert body["success"] is False
    assert body["api_code"] == 20001, f"应该是 20001，实际 {body['api_code']}"

    cat = await _wait_cat(adoptable_id, lambda c: c.status == "审核中")
    assert cat.applicant_id == alice, "第一个申请人不能被覆盖"


async def test_adopt_already_adopted_rejected(client, two_cats, three_users):
    """抢一只已领养的猫 → 20001。"""
    _, taken_id = two_cats

    res = await client.post(
        f"/api/v1/cats/{taken_id}/adopt", headers=_headers(three_users[2])
    )
    body = res.json()
    assert body["success"] is False
    assert body["api_code"] == 20001


async def test_adopt_concurrent_only_one_wins(client):
    """★ 并发 10 个不同用户抢同一只猫：恰好 1 个成功，赢家是这 10 人之一。

    这是"一只猫只能被一人申请"的唯一可信验证方式。
    串行地测两次申请，看不出竞态；并发才看得出。
    """
    async with AsyncSessionLocal() as db:
        cat = Cat(name="_t_并发", breed="狸花", city="深圳", status="待领养")
        db.add(cat)
        await db.commit()
        cat_id = cat.id

    user_ids = await _make_users(10)
    try:
        async def hit(i):
            resp = await client.post(
                f"/api/v1/cats/{cat_id}/adopt", headers=_headers(user_ids[i])
            )
            return resp.json().get("api_code")

        codes = await asyncio.gather(*[hit(i) for i in range(10)])

        successes = [c for c in codes if c == 200]
        rejected = [c for c in codes if c == 20001]

        assert len(successes) == 1, (
            f"并发 10 个应该只有 1 个成功，实际成功 {len(successes)} 个：{codes}"
        )
        assert len(rejected) == 9, f"应该有 9 个被拒，实际 {len(rejected)} 个：{codes}"

        cat = await _wait_cat(cat_id, lambda c: c.status == "审核中")
        assert cat.status == "审核中"
        assert cat.applicant_id in user_ids, "赢家必须是这 10 个真实用户之一"
    finally:
        await _cleanup([cat_id], user_ids)
