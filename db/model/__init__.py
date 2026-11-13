# db/model/__init__.py
# =============================================================================
# ★ 每新增一个模型文件，都要在这里 import 一次并加进 __all__。
#   原因：main.py 里的 create_all 依赖 Base.metadata，
#   而模型只有被 import 过一次，才会注册到 metadata 里。
#   漏了这一步 → 建表时"这张表不存在"，但代码里又能 import 到类，很难查。
# =============================================================================
from db.model.Content import Content
from db.model.UserEvent import UserEvent
from db.database import Base

__all__ = ["Base", "Content", "UserEvent"]

# 示例（以后照这个加）：
# from db.model.Content import Content
# from db.model.Cat import Cat
# from db.model.UserEvent import UserEvent
# __all__ += ["Content", "Cat", "UserEvent"]
