from grpc_frame.grpc_server import create_grpc_server
from cap_inspector import CapInspector
from x_logger import XLogger

#HOST = "0.0.0.0"
HOST = "10.170.10.55"
PORT = 50051
ADDRESS = f"{HOST}:{PORT}"

GRPC_OPTIONS = (
    ("grpc.max_send_message_length", 16 * 1024 * 1024),
    ("grpc.max_receive_message_length", 16 * 1024 * 1024),
)

logger = XLogger(logger_name="cap_inspector_server")
logger.info("CapInspector server initialization started")
logger.info(f"gRPC address: {ADDRESS}")
logger.info(f"gRPC options: {GRPC_OPTIONS}")

cap = CapInspector(camera_id=0, logger=logger)
logger.info("CapInspector instance created")

server = create_grpc_server(
    ctrl_obj=cap,
    stream_obj=cap,
    grpc_options=GRPC_OPTIONS,
    logger=logger,
)
logger.info("grpc_frame server created")

server.add_insecure_port(ADDRESS)
server.start()
logger.info(f"CapInspector server started: {ADDRESS}")

try:
    server.wait_for_termination()
except KeyboardInterrupt:
    logger.info("Server stop requested by keyboard interrupt")
finally:
    logger.info("CapInspector server shutdown started")
    cap.release()
    logger.info("CapInspector server shutdown completed")
