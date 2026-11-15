from sqlalchemy import update

from db.model import Cat


async def adopt_cat(db, cat_id: int, user_id: int) -> bool:
    """原子抢占：成功 True，被别人抢走 False。

    ★ 关键：把"检查状态"和"修改状态"压进同一条 UPDATE，
      绝不允许先 select 再 if 判断再改（那会有 TOCTOU 竞态）。
    """
    stmt = update(Cat).where(
        Cat.id == cat_id,       # 条件1：哪只猫（这里用 == 是对的，因为它是"比较"）
        Cat.status == "待领养",  # 条件2：状态还是"待领养"（只有这样才能改）
    ).values(
        status="审核中",         # ★ values 里是"赋值"：键=列名，用 = 
        applicant_id=user_id,   # ★ 申请不等于领养成功，所以是"审核中"不是"已领养"
    )
    result = await db.execute(stmt)
    return result.rowcount == 1    # 怎么判断抢到了？提示：和你挂号那行一样
