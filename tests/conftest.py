# =============================================================================
# tests/conftest.py —— pytest 的公共装置（fixture 都放这）
# =============================================================================
# 【怎么测一个异步 FastAPI 应用】
#   不启动 uvicorn，也不占端口：用 httpx 的 ASGITransport 直接把请求「喂」给 app。
#   这样测的是同一份 app 代码，但不用管端口、不用管进程。
#
# 【为什么要一个 session 级的 client】
#   db/database.py 里的 async_engine 是模块导入时就创建的，
#   连接池里的真实连接绑定在「第一次使用它的 event loop」上。
#   如果每个测试都新建 loop，第二个用数据库的测试就会拿到别的 loop 的连接，报：
#       AttributeError: 'NoneType' object has no attribute 'send'
#   所以这里用 scope="session"：整个测试过程只跑在一个 loop 里。
#
# 【前置条件】
#   MySQL 必须开着（db/database.py 的 lifespan 会 SELECT 1），
#   .env 必须存在（否则 utils/auth.py 会拒绝启动）。
# =============================================================================
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import app


@pytest_asyncio.fixture(scope="session")
async def client():
    """整个测试会话共用一个 HTTP 客户端（同一 loop，同一份 app）。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

