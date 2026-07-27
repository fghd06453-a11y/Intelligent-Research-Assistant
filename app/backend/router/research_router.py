import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.backend.schemas import ResearchRequest, ResearchResponse  #看图标，有句号的图标就是可以被导入的包（同时看有没有_init_.py文件），没有就是普通目录，
from app.backend.service import WorkflowService, get_workflow_service


router = APIRouter(prefix="/api/v1/research", tags=["research"])


@router.post("/run", response_model=ResearchResponse)
async def run_research(
    payload: ResearchRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),
) -> ResearchResponse:
    final = await workflow_service.run(
        query=payload.query,
        user_id=payload.user_id,
        thread_id=payload.thread_id,
        tenant_id=payload.tenant_id,
        max_iterations=payload.max_iterations,
        enable_memory=payload.enable_memory,
    )
    return ResearchResponse(
        query=payload.query,
        user_id=payload.user_id,
        thread_id=payload.thread_id,
        tenant_id=payload.tenant_id,
        final=final,
    )


@router.post("/stream")
async def stream_research(
    payload: ResearchRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service),   # “= Depends()” 懒加载，路由接收到请求，框架先加载这个函数，
                                                                         # #即获得WorkflowService实例，因为get_workflow_service 有@lru_cache注解，#
                                                                         # 第二次收到这个请求时使用缓存的实例，不会新建一个实例，所以第一次请求加载时间长，SSE容易超时
) -> StreamingResponse:
    async def event_stream():
        start_event = {"type": "status", "message": "任务已接收，正在初始化多智能体链路"}
        yield f"data: {json.dumps(start_event, ensure_ascii=False)}\n\n"
        async for event in workflow_service.stream_events(
            query=payload.query,
            user_id=payload.user_id,
            thread_id=payload.thread_id,
            tenant_id=payload.tenant_id,
            max_iterations=payload.max_iterations,
            enable_memory=payload.enable_memory,
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")   # SSE 事件流，media_type="text/event-stream"告诉前端如何解析，
                                                                               # #具体按照f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
