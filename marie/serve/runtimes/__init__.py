
def get_runtime(name: str):
    """Get a public runtime by its name

    # noqa: DAR101
    # noqa: DAR201
    """
    from marie.serve.runtimes.base import BaseRuntime
    # from jina.serve.runtimes.gateway.grpc import GRPCGatewayRuntime
    # from jina.serve.runtimes.gateway.http import HTTPGatewayRuntime
    # from jina.serve.runtimes.gateway.websocket import WebSocketGatewayRuntime
    # from jina.serve.runtimes.worker import WorkerRuntime
    # from jina.serve.runtimes.head import HeadRuntime

    s = locals()[name]
    if isinstance(s, type) and issubclass(s, BaseRuntime):
        return s
    else:
        raise TypeError(f'{s!r} is not in type {BaseRuntime!r}')
