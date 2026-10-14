from cap_inspector.server_grpc import cap_inspector_server
from x_logger import XLogger

# HOST = "10.170.10.55"
HOST = "127.0.0.1"
PORT = 50051


if __name__ == "__main__":
    logger = XLogger(logger_name="cap_inspector_server")
    cap_inspector_server(
        grpc_host=HOST,
        grpc_port=PORT,
        camera_id=0,
        logger=logger,
    )
