# apis/__init__.py
# 每个业务模块一个子目录，结构固定为：
#   apis/<模块>/
#     api/            路由（知道 HTTP）
#     schemas/        出入参 Pydantic 模型
#     repository/     只写 SQL
#     dependencies/   本模块专用依赖
