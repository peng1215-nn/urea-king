import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# 在读取环境变量之前先加载 .env，避免依赖其他模块的导入顺序
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # 不再静默回退到本地 SQLite：漏配时直接报错，避免悄悄写进一个会随部署丢失的文件库
    raise RuntimeError(
        "DATABASE_URL is not set. Please configure it in .env or environment variables."
    )

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )

connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    # 报错信息里不带 SQL 参数的值（邮箱、令牌、密码哈希），避免写进日志和 Sentry
    hide_parameters=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()