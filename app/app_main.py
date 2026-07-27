"""智能研究系统 — Web 模式启动入口（FastAPI + LangGraph 多智能体工作流）。"""

import sys
from pathlib import Path

# 将项目根目录加入 sys.path，确保 app.xxx 和 backend.xxx 均可导入
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import AppSettings
from backend.router import health_router, research_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logging.getLogger("mult_agents").setLevel(logging.INFO)
logging.getLogger("backend").setLevel(logging.INFO)


def create_app() -> FastAPI:
    settings = AppSettings()
    app = FastAPI(title=settings.app_name)
    # 添加跨域中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)  #挂载路由后，才能接收请求
    app.include_router(research_router)
    return app


app = create_app()


if __name__ == "__main__":
    runtime_settings = AppSettings()
    uvicorn.run(
        "app_main:app",
        host=runtime_settings.host,
        port=runtime_settings.port,
        reload=runtime_settings.app_env == "development",
    )
