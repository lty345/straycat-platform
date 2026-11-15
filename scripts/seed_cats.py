# =============================================================================
# scripts/seed_cats.py —— 造待领养的猫（含 1 只已领养，用来测"抢不到"）
# =============================================================================
# 用法（项目根目录）：
#   uv run python scripts/seed_cats.py
#
# 【为什么这么造】
#   领养抢占要验证三种情况，所以数据里必须有：
#     ① 待领养状态（能抢）—— 5 只
#     ② 已领养状态（抢不到，返回 20001）—— 1 只
#     ③ 其中 1 只专门留给并发测试（10 个请求同时抢，只该成功 1 个）
#   城市和内容的城市对齐（广州/深圳/佛山），方便演示"同城"
#
# 【幂等】每次先清空 cat 表再插入。
# =============================================================================
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import delete, select

from db.database import AsyncSessionLocal, async_engine
from db.model import Cat

# (名字, 品种, 月龄, 健康, 城市, 状态, 封面序号)
SEED = [
    ("小橘", "橘猫", 8, "已驱虫、已绝育", "广州", "待领养", 1),
    ("煤球", "黑猫", 14, "已驱虫", "广州", "待领养", 2),
    ("大福", "狸花", 24, "已驱虫、已绝育", "深圳", "待领养", 3),
    ("奶糖", "三花", 5, "已驱虫、待绝育", "深圳", "待领养", 4),
    ("阿灰", "狸花", 36, "已绝育", "佛山", "待领养", 5),
    ("老白", "白猫", 60, "慢性肾病，需长期用药", "佛山", "已领养", 6),
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Cat))

        rows = [
            Cat(
                name=name,
                breed=breed,
                age_month=age,
                health=health,
                city=city,
                status=status,
                # 已领养的猫要有个领养人，否则"已领养"这条记录是不完整的
                applicant_id=4 if status == "已领养" else None,
                # 封面复用已有的 p01~p24（web/public/covers 里只有这批图，
                # 之前写的 catNN.jpg 并不存在，会导致 404）
                cover_url=f"/covers/p{pic:02d}.jpg",
            )
            for name, breed, age, health, city, status, pic in SEED
        ]
        db.add_all(rows)
        await db.commit()

        all_rows = (await db.execute(select(Cat))).scalars().all()

    print(f"完成：cat 表共 {len(all_rows)} 只")
    for c in all_rows:
        print(f"  id={c.id}  {c.name:<4} {c.breed:<4} {c.city:<4} {c.status}")

    wait = [c for c in all_rows if c.status == "待领养"]
    print(f"\n待领养 {len(wait)} 只（可抢）｜已领养 {len(all_rows) - len(wait)} 只（抢会失败）")
    if wait:
        print(f"并发测试建议用 id={wait[0].id}（{wait[0].name}）")

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
