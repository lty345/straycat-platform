# =============================================================================
# scripts/seed_users_events.py —— 造 3 个用户 + 50 条埋点
# =============================================================================
# 用法（在项目根目录）：
#   uv run python scripts/seed_users_events.py
#   或 .venv\Scripts\python.exe scripts\seed_users_events.py
#
# 【为什么这么造】
#   推荐算法的验证标准是「两个兴趣不同的用户，/feed 顺序明显不同」。
#   要验证这一点，种子数据必须满足：
#     ① 用户兴趣**真的不同**：小橘偏"橘猫/日常"，阿救偏"救助/科普"
#     ② 行为**指向兴趣**：小橘浏览/点赞的内容，标签就是她感兴趣的
#     ③ 留一个**冷启动用户**（没有兴趣标签、没有行为）→ 用来测热门兜底
#
# 【幂等】每次先清空 app_user / user_event 再插入，跑多少次结果都一样。
# =============================================================================
import asyncio
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ★ 直接 `python scripts/xxx.py` 时，sys.path 里是 scripts/ 而不是项目根，
#   `from db.database import ...` 会报 ModuleNotFoundError。
#   这里把项目根塞进 sys.path，脚本就能在任何目录直接跑，不用设 PYTHONPATH。
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK，中文会乱码

from sqlalchemy import delete, select

from db.database import AsyncSessionLocal, async_engine
from db.model import AppUser, Content, UserEvent

# ---- 三个用户（第三个是冷启动样本）----------------------------------------
USERS = [
    {"nickname": "小橘", "city": "广州", "interest_tags": "橘猫,日常,治愈向"},
    {"nickname": "阿救", "city": "深圳", "interest_tags": "救助,奶猫,领养"},
    {"nickname": "路过的新人", "city": "广州", "interest_tags": None},
]

# ---- 每个用户"感兴趣"的标签：行为会集中在这些标签的内容上 -------------------
INTERESTS = {
    "小橘": ["橘猫", "日常", "治愈向", "行为", "陪伴"],
    "阿救": ["救助", "奶猫", "领养", "科普", "信任"],
}

VIEWS_PER_USER = 20
LIKES_PER_USER = 5


def tag_set(tags: str | None) -> set[str]:
    return {t.strip() for t in (tags or "").split(",") if t.strip()}


async def seed() -> None:
    random.seed(20261114)  # 固定随机种子，保证每次造出来的数据一样

    async with AsyncSessionLocal() as db:
        # ① 清空（幂等）
        await db.execute(delete(UserEvent))
        await db.execute(delete(AppUser))
        await db.commit()

        # ② 插用户
        users = [AppUser(**u) for u in USERS]
        db.add_all(users)
        await db.commit()
        await db.refresh(users[0])  # 触发一次读，确保 id 已回填
        user_map = {u.nickname: u.id for u in users}

        # ③ 取所有内容（用于按标签挑目标）
        contents = (await db.execute(select(Content))).all()
        contents = [c[0] for c in contents]
        if not contents:
            print("⚠️ content 表是空的，先跑 scripts/seed_content.py")
            return

        # ④ 给前两个用户造行为：浏览/点赞集中在他们感兴趣的标签上
        now = datetime.now()
        events: list[UserEvent] = []

        for nickname, interest_tags in INTERESTS.items():
            uid = user_map[nickname]

            # 按"命中兴趣标签的数量"排序，命中的优先被看
            def score(c: Content) -> int:
                return len(tag_set(c.tags) & set(interest_tags))

            ranked = sorted(contents, key=score, reverse=True)
            matched = [c for c in ranked if score(c) > 0]
            others = [c for c in ranked if score(c) == 0]

            # ★ 凑够 20 条浏览：先看感兴趣的，再看"顺带刷到的"，
            #   还不够就重复看（真实世界里同一篇看两次很常见）。
            target_pool = (matched + others)
            while len(target_pool) < VIEWS_PER_USER:
                target_pool += matched or others
            target_pool = target_pool[:VIEWS_PER_USER]

            # 浏览：前 20 条，时间分散在最近 3 天
            for i, c in enumerate(target_pool[:VIEWS_PER_USER]):
                events.append(
                    UserEvent(
                        user_id=uid,
                        target_type="content",
                        target_id=c.id,
                        event="view",
                        duration_ms=random.randint(3000, 120000),
                        create_time=now - timedelta(minutes=90 * i + random.randint(0, 30)),
                    )
                )

            # 点赞：从最匹配的内容里挑，且时间更近（表示"更喜欢"）
            for i, c in enumerate(target_pool[:LIKES_PER_USER]):
                events.append(
                    UserEvent(
                        user_id=uid,
                        target_type="content",
                        target_id=c.id,
                        event="like",
                        create_time=now - timedelta(minutes=30 * i),
                    )
                )

        # ⑤ 第三个用户（路过的新人）不产生任何行为 —— 冷启动样本
        db.add_all(events)
        await db.commit()

        # ⑥ 回读确认
        total_users = len((await db.execute(select(AppUser))).all())
        total_events = len((await db.execute(select(UserEvent))).all())

    print(f"完成：用户 {total_users} 个，埋点 {total_events} 条")
    print("  小橘（广州，橘猫/日常）→ 25 条行为")
    print("  阿救（深圳，救助/奶猫）→ 25 条行为")
    print("  路过的新人（广州，无标签无行为）→ 冷启动样本")
    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
