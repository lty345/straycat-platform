from sqlalchemy import func, select, update

from db.model import Cat


# -----------------------------------------------------------------------------
# 一、抢占（写）
# -----------------------------------------------------------------------------
async def adopt_cat(db, cat_id: int, user_id: int) -> bool:
    """原子抢占：成功 True，被别人抢走 False。

    ★ 关键：把"检查状态"和"修改状态"压进同一条 UPDATE，
      绝不允许先 select 再 if 判断再改（那会有 TOCTOU 竞态）。
    """
    stmt = update(Cat).where(
        Cat.id == cat_id,       # 条件1：哪只猫（这里用 ==，因为它是"比较"）
        Cat.status == "待领养",  # 条件2：状态还是"待领养"才允许改
    ).values(
        status="审核中",         # values 里是"赋值"：键=列名
        applicant_id=user_id,   # 申请不等于领养成功，所以是"审核中"而非"已领养"
    )
    result = await db.execute(stmt)
    # 成败只看 rowcount：1 = 抢到，0 = 状态已被别人改掉（并发下必然只有一个 1）
    return result.rowcount == 1


async def get_cat_by_id(db, cat_id: int) -> Cat | None:
    """按 id 查一只猫（只用于"报错文案"，不用于判断抢占成败）。"""
    return (
        await db.execute(select(Cat).where(Cat.id == cat_id))
    ).scalar_one_or_none()


# -----------------------------------------------------------------------------
# 一·补、审核（状态机闭环：审核中 → 已领养 / 待领养）
# -----------------------------------------------------------------------------
# ★ 这里和抢占是**同一套 CAS**，只是条件从"待领养"换成了"审核中"：
#     - 通过：UPDATE ... WHERE id=? AND status='审核中'
#     - 驳回：同一条，只是把状态改回"待领养"并清空申请人
#   为什么不能"先查再改"：两个管理员同时点"通过/驳回"，
#   会一个通过、一个驳回，最终状态取决于谁最后提交 —— 又是 TOCTOU。
# -----------------------------------------------------------------------------
async def approve_cat(db, cat_id: int) -> bool:
    """审核通过：审核中 → 已领养。成功 True，状态不对 False。"""
    stmt = (
        update(Cat)
        .where(
            Cat.id == cat_id,
            Cat.status == "审核中",     # ← 只有"审核中"才能通过
        )
        .values(status="已领养")
    )
    return (await db.execute(stmt)).rowcount == 1


async def reject_cat(db, cat_id: int) -> bool:
    """审核驳回：审核中 → 待领养，并清空申请人（让猫重新开放给别人申请）。"""
    stmt = (
        update(Cat)
        .where(
            Cat.id == cat_id,
            Cat.status == "审核中",
        )
        .values(
            status="待领养",
            applicant_id=None,          # 驳回要把申请人清掉，否则这只猫"挂着别人的名字"
        )
    )
    return (await db.execute(stmt)).rowcount == 1


# -----------------------------------------------------------------------------
# 二、列表（读）
# -----------------------------------------------------------------------------
def _apply_filters(stmt, status: str | None, city: str | None):
    """把筛选条件拼到语句上。

    ★ 为什么抽出来：list 和 count 必须用**同一套** where，
      否则 total 和实际能翻到的条数对不上（这个坑在 event 模块踩过）。
    """
    if status:
        stmt = stmt.where(Cat.status == status)
    if city:
        stmt = stmt.where(Cat.city == city)
    return stmt


async def list_cats(
    db,
    offset: int = 0,
    limit: int = 20,
    status: str | None = None,
    city: str | None = None,
) -> list[Cat]:
    """分页查猫。

    ★ 显式 order_by：不加排序时 MySQL 不保证顺序，翻页会出现重复/漏条。
      用 id 升序（猫的数量少、且用户更关心"先登记的"），
      想改成"新登记的在前"只需换成 Cat.id.desc()。
    """
    stmt = select(Cat)
    stmt = _apply_filters(stmt, status, city)
    stmt = stmt.order_by(Cat.id.asc()).offset(offset).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def count_cats(db, status: str | None = None, city: str | None = None) -> int:
    """符合条件的总条数（和 list_cats 共用同一套 where）。"""
    stmt = _apply_filters(select(func.count()).select_from(Cat), status, city)
    return (await db.execute(stmt)).scalar_one()
