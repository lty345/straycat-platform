from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache



class Settings(BaseSettings):
    # ★ 告诉 pydantic-settings：去读项目根目录的 .env 文件
    #   不加这一行，.env 建了也不会生效（只读系统环境变量）
    #   extra="ignore"：环境里有别的变量时忽略，不报错
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ASYNC_DB_DRIVER:str=("mysql+aiomysql")
    ASYNC_DB_HOST:str="localhost"
    ASYNC_DB_PORT:int=3306
    ASYNC_DB_USER:str="root"
    # ★ 不再写死密码：真实值放 .env（.env 已在 .gitignore 中）
    ASYNC_DB_PASSWORD:str=""
    ASYNC_DB_DATABASE:str="straycat"
    ASYNC_DB_ECHO:bool=False
    ASYNC_DB_POOL_SIZE:int=60
    ASYNC_DB_MAX_OVERFLOW:int=0

    # ★ JWT 签名密钥：同样只从 .env 读，没配就由 auth.py 拒绝启动
    SECRET_KEY:str=""

    GZX_ID:str=""
    GZX_SECRET:str=""
    GEX_PAY_KEY:str=""
    MCH_ID:str=""
    NOTIFY_URL:str="http://xxx/api/v1/doctor/subscribe/paycallback"
    GZX_REDIRECT_URI: str = ""

@lru_cache()
def get_settings():
    return Settings()