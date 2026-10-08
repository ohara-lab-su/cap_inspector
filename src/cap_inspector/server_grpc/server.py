from typing import Any, Optional, Sequence, Tuple

from grpc_frame.grpc_server import create_grpc_server

from cap_inspector.cap_inspector import CapInspector


def cap_inspector_server(
    *,
    grpc_host: str,
    grpc_port: int,
    camera_id: int = 0,
    grpc_options: Optional[Sequence[Tuple[str, Any]]] = None,
    logger: Optional[Any] = None,
) -> None:
    """CapInspector を grpc_frame 上で公開するサーバーを起動する。"""
    if grpc_options is None:
        grpc_options = (
            ("grpc.max_send_message_length", 16 * 1024 * 1024),
            ("grpc.max_receive_message_length", 16 * 1024 * 1024),
        )

    cap = CapInspector(camera_id=camera_id, logger=logger)
    server = create_grpc_server(
        ctrl_obj=cap,
        stream_obj=cap,
        grpc_options=grpc_options,
        logger=logger,
    )

    address = str(grpc_host) + ":" + str(grpc_port)
    ret = server.add_insecure_port(address)
    if ret == 0:
        cap.release()
        raise RuntimeError("bind failed: " + address)

    if logger is not None:
        logger.info("CapInspector server started: " + address)

    server.start()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        if logger is not None:
            logger.info("Server stop requested by keyboard interrupt")
    finally:
        server.stop(grace=None)
        cap.release()
        if logger is not None:
            logger.info("CapInspector server shutdown completed")
