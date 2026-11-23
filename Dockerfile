# =============================================================================
# Dockerfile —— 后端 FastAPI 镜像（云托管容器用）
# =============================================================================
# 为什么手写依赖列表而不 `pip install .`：
#   这个项目是按目录组织的应用（apis/ services/ db/），不是可安装的 Python 包；
#   直接 pip install . 会因为没有 packages 配置而失败。
#   所以显式列出运行时依赖，构建更可控也更快。
# =============================================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 1) 先装依赖（利用 Docker 层缓存：只改代码时不用重装）
#    ★ 用阿里云 PyPI 镜像：国内直连 pypi.org 极慢甚至超时
#      （如果你在海外部署，把 PIP_INDEX 换成 https://pypi.org/simple 即可）
ARG PIP_INDEX=https://mirrors.aliyun.com/pypi/simple/
RUN pip install --no-cache-dir -i ${PIP_INDEX} \
    "fastapi[standard]>=0.148.0" \
    "uvicorn[standard]>=0.54.0" \
    "sqlalchemy[asyncio]>=2.1.5" \
    "asyncpg>=0.29.0" \
    "aiomysql>=0.3.2" \
    "pydantic-settings>=2.16.0" \
    "loguru>=0.7.3" \
    "cryptography>=50.0.2" \
    "python-jose>=3.5.0" \
    "bcrypt>=5.0.0" \
    "httpx>=0.28.1" \
    "pillow>=13.0.0"

# 2) 再拷代码
COPY . .

# 3) 云托管默认监听 8080（可用 PORT 覆盖）
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
