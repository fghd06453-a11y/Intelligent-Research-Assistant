"""Agent 工厂模块：构建智能体、Checkpointer 和 MemoryManager。"""

import importlib
import logging
import os
from dataclasses import dataclass
from typing import Optional

from langchain_community.chat_models import ChatTongyi
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

from .config import AppConfig
from .memory import MemoryManager
from .prompts import PROMPTS
from .tools import init_rag_system
from .rag.core import RAGConfig

logger = logging.getLogger("mult_agents")
CHECKPOINTER_CONTEXT = None


def build_memory_manager(config: AppConfig) -> Optional[MemoryManager]:
    """初始化 MemoryManager（Redis + PostgreSQL + Milvus）。"""
    if not config.enable_memory:
        return None
    try:
        return MemoryManager(
            short_term_ttl=config.short_term_ttl_seconds,
            short_term_max_messages=config.short_term_max_messages,
            short_term_summary_threshold=config.short_term_summary_threshold,
            tenant_id=config.tenant_id,
            short_term_backend=config.short_term_backend,
            long_term_backend=config.long_term_backend,
            long_term_scope=config.long_term_scope,
            save_conversation_task=config.save_conversation_task,
            enable_milvus=config.enable_milvus,
            redis_url=config.redis_url,
            postgres_dsn=config.postgres_dsn,
            milvus_host=config.milvus_host,
            milvus_port=config.milvus_port,
            milvus_collection=config.milvus_collection,
            embedding_api_key=config.api_key,
        )
    except Exception as exc:
        logger.exception("MemoryManager 初始化失败: %s", exc)
        return None


def build_checkpointer(config: AppConfig):
    """初始化 Checkpointer（PostgreSQL > Redis > 内存）。"""
    global CHECKPOINTER_CONTEXT
    backend = config.checkpointer_backend

    # PostgreSQL
    if backend in {"postgres", "auto"} and config.enable_memory and config.postgres_dsn:
        postgres_saver = None
        postgres_import_error = ""
        try:
            module = importlib.import_module("langgraph.checkpoint.postgres")   #动态导入 langgraph.checkpoint.postgres 模块
            postgres_saver = getattr(module, "PostgresSaver", None)
        except Exception as exc:
            postgres_import_error = str(exc)
        if postgres_saver is None:
            try:
                module = importlib.import_module("langgraph_checkpoint_postgres")
                postgres_saver = getattr(module, "PostgresSaver", None)
            except Exception as exc:
                postgres_import_error = postgres_import_error or str(exc)
        if postgres_saver is None:
            logger.warning(
                "PostgreSQL checkpointer 不可用: %s", postgres_import_error or "unknown"
            )
        else:
            try:
                CHECKPOINTER_CONTEXT = postgres_saver.from_conn_string(config.postgres_dsn)
                checkpointer = CHECKPOINTER_CONTEXT.__enter__()
                checkpointer.setup()
                logger.info("使用 PostgreSQL checkpointer")
                return checkpointer
            except Exception as exc:
                logger.warning("PostgreSQL checkpointer 初始化失败: %s", exc)

    # Redis
    if backend in {"redis", "auto"} and config.enable_memory and config.redis_url:
        from langgraph.checkpoint.redis import RedisSaver

        candidate_urls = [config.redis_url]
        if "redis://root:" in config.redis_url:
            candidate_urls.append(config.redis_url.replace("redis://root:", "redis://:"))
        last_exc = None
        for url in candidate_urls:
            try:
                CHECKPOINTER_CONTEXT = RedisSaver.from_conn_string(url)
                checkpointer = CHECKPOINTER_CONTEXT.__enter__()
                checkpointer.setup()
                logger.info("使用 Redis checkpointer")
                return checkpointer
            except Exception as exc:
                last_exc = exc
        if last_exc and "FT._LIST" in str(last_exc):
            logger.warning("Redis checkpointer 依赖 RediSearch，已降级")
        else:
            logger.warning("Redis checkpointer 初始化失败，降级内存: %s", last_exc)

    # 内存（最终降级）
    logger.info("使用内存 checkpointer")
    return InMemorySaver()


@dataclass(frozen=True)
class AgentBundle:
    """Agent 集合，注入 LangGraph 工作流。"""
    intent_router: any
    planner: any
    scout_web: any
    scout_local: any
    evidence_judge: any
    analyst: any
    direct_responder: any
    writer: any


def build_agent(model: str, api_key: str, prompt_key: str, temperature: float, tools: list):
    """创建单个 Agent。"""
    if api_key:
        os.environ["DASHSCOPE_API_KEY"] = api_key
    llm = ChatTongyi(model=model, temperature=temperature, request_timeout=600)
    prompt = PROMPTS[prompt_key]
    return create_agent(model=llm, tools=tools, system_prompt=prompt)


def build_agents(model: str, api_key: str, config: AppConfig) -> AgentBundle:
    """创建全部 8 个 Agent。"""
    rag_config = RAGConfig(
        milvus_host=config.milvus_host,
        milvus_port=config.milvus_port,
        collection_name=config.milvus_collection,
    )
    init_rag_system(api_key=api_key, config=rag_config)
    return AgentBundle(
        intent_router=build_agent(model, api_key, "intent_router", 0.0, []),
        planner=build_agent(model, api_key, "plan", 0.3, []),
        scout_web=build_agent(model, api_key, "web_search", 0.4, []),
        scout_local=build_agent(model, api_key, "local_rag", 0.4, []),
        evidence_judge=build_agent(model, api_key, "deep_dive", 0.2, []),
        analyst=build_agent(model, api_key, "analyze", 0.3, []),
        direct_responder=build_agent(model, api_key, "direct_answer", 0.2, []),
        writer=build_agent(model, api_key, "write", 0.4, []),
    )
