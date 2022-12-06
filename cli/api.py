from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

from typing import TYPE_CHECKING

from marie.parsers.helper import _update_gateway_args

if TYPE_CHECKING:
    from argparse import Namespace


def deployment(args: 'Namespace'):
    """
    Start a Deployment

    :param args: arguments coming from the CLI.
    """
    from marie.orchestrate.deployments import Deployment

    try:
        with Deployment(args) as d:
            d.join()
    except KeyboardInterrupt:
        pass


def pod(args: 'Namespace'):
    """
    Start a Pod

    :param args: arguments coming from the CLI.
    """
    from marie.orchestrate.pods.factory import PodFactory

    try:
        with PodFactory.build_pod(args) as p:
            p.join()
    except KeyboardInterrupt:
        pass


def executor_native(args: 'Namespace'):
    """
    Starts an Executor in a WorkerRuntime

    :param args: arguments coming from the CLI.
    """

    if args.runtime_cls == 'WorkerRuntime':
        from marie.serve.runtimes.worker import WorkerRuntime

        runtime_cls = WorkerRuntime
    elif args.runtime_cls == 'HeadRuntime':
        from marie.serve.runtimes.head import HeadRuntime

        runtime_cls = HeadRuntime
    else:
        raise RuntimeError(
            f' runtime_cls {args.runtime_cls} is not supported with `--native` argument. `WorkerRuntime` is supported'
        )

    with runtime_cls(args) as rt:
        name = (
            rt._worker_request_handler._executor.metas.name
            if hasattr(rt, '_worker_request_handler')
            else rt.name
        )
        rt.logger.info(f'Executor {name} started')
        rt.run_forever()


def executor(args: 'Namespace'):
    """
    Starts an Executor in any Runtime

    :param args: arguments coming from the CLI.

    :returns: return the same as `pod` or `worker_runtime`
    """
    if args.native:
        return executor_native(args)
    else:
        return pod(args)


def worker_runtime(args: 'Namespace'):
    """
    Starts a WorkerRuntime

    :param args: arguments coming from the CLI.
    """
    from marie.serve.runtimes.worker import WorkerRuntime

    with WorkerRuntime(args) as runtime:
        runtime.logger.info(
            f'Executor {runtime._worker_request_handler._executor.metas.name} started'
        )
        runtime.run_forever()


def gateway(args: 'Namespace'):
    """
    Start a Gateway Deployment

    :param args: arguments coming from the CLI.
    """
    from marie.serve.runtimes import get_runtime

    _update_gateway_args(args)

    runtime_cls = get_runtime('GatewayRuntime')

    with runtime_cls(args) as runtime:
        runtime.logger.info(f'Gateway started')
        runtime.run_forever()


def ping(args: 'Namespace'):
    """
    Check the connectivity of a Pod

    :param args: arguments coming from the CLI.
    """
    from marie.checker import NetworkChecker

    NetworkChecker(args)


#
# def dryrun(args: 'Namespace'):
#     """
#     Check the health of a Flow
#
#     :param args: arguments coming from the CLI.
#     """
#     from marie.checker import dry_run_checker
#
#     dry_run_checker(args)
#
#
# def client(args: 'Namespace'):
#     """
#     Start a client connects to the gateway
#
#     :param args: arguments coming from the CLI.
#     """
#     from jina.clients import Client
#
#     Client(args)
#
#
# def export(args: 'Namespace'):
#     """
#     Export the API
#
#     :param args: arguments coming from the CLI.
#     """
#     from marie import exporter
#
#     getattr(exporter, f'export_{args.export.replace("-", "_")}')(args)


def flow(args: 'Namespace'):
    """
    Start a Flow from a YAML file or a docker image

    :param args: arguments coming from the CLI.
    """
    from marie import Flow

    if args.uses:
        f = Flow.load_config(args.uses)
        with f:
            f.block()
    else:
        raise ValueError('start a flow from CLI requires a valid `--uses`')


def hub(args: 'Namespace'):
    """
    Start a hub builder for push, pull
    :param args: arguments coming from the CLI.
    """
    pass


def new(args: 'Namespace'):
    """
    Create a new jina project
    :param args:  arguments coming from the CLI.
    """
    import os
    import shutil

    from marie import __resources_path__

    shutil.copytree(
        os.path.join(__resources_path__, 'project-template'), os.path.abspath(args.name)
    )


def help(args: 'Namespace'):
    """
    Lookup the usage of certain argument in Marie API.

    :param args: arguments coming from the CLI.
    """
    from cli.lookup import lookup_and_print

    lookup_and_print(args.query.lower())


def auth(args: 'Namespace'):
    """
    Authenticate a user
    :param args: arguments coming from the CLI.
    """
    pass


def cloud(args: 'Namespace'):
    """
    Use jcloud (Jina Cloud) commands
    :param args: arguments coming from the CLI.
    """
    pass