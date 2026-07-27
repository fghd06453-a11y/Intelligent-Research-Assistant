from functools import lru_cache

from .workflow_service import WorkflowService

# @lru_cache 这个注解表示下一次的入参与第一次相同时，直接将缓存里的结果返回，不会重新执行这个函数，参数应避免可变，  @lru_cache注解作用域仅限单个进程
#每次只使用同一个 WorkflowService()实例，

@lru_cache(maxsize=1)
def get_workflow_service() -> WorkflowService:
    return WorkflowService()


__all__ = ["WorkflowService", "get_workflow_service"]
