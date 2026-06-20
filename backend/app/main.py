"""FastAPI 应用入口。"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.logging_config import setup_logging
from app.models import Role, User
from app.routers import admin, auth, interview
from app.security import hash_password

setup_logging()
logger = logging.getLogger(__name__)


async def init_db():
    logger.info("初始化数据库：创建表 ...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 初始化管理员账号
    async with SessionLocal() as db:
        exists = (
            await db.execute(select(User).where(User.username == settings.admin_username))
        ).scalar_one_or_none()
        if not exists:
            db.add(User(
                username=settings.admin_username,
                hashed_password=hash_password(settings.admin_password),
                role=Role.admin,
            ))
            await db.commit()
            logger.info("已创建初始管理员账号：%s", settings.admin_username)
        else:
            logger.info("管理员账号已存在：%s", settings.admin_username)
    logger.info("数据库初始化完成")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("应用启动中 ... LLM 模型=%s base=%s", settings.llm_model, settings.openai_base_url)
    await init_db()
    logger.info("应用启动完成 ✅")
    yield
    logger.info("应用关闭")


# uv run uvicorn app.main:app --reload --port 8002
#构建镜像：docker build -t interview-backend:20260620-001 .
#运行容器并映射端口：docker run -p 8002:8002 interview-backend:20260620-001
#或者
#docker-compose.yml文件部署 docker compose up -d
#之后可通过 http://localhost:8002 访问你的 API 服务。
app = FastAPI(title="智能面试系统", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(interview.router)


@app.get("/")
async def root():
    return {"service": "智能面试系统", "docs": "/docs"}
