# services/__init__.py
# 跨表 / 跨模块的业务编排放这里（如：领养抢占、推荐打分）。
# 规矩：service 不许出现 HTTPException，也不许写 select/update。
# 它只负责"按业务规则判断和串联"，取数据交给 repository。
