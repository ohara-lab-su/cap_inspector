from grpc_frame.grpc_server import create_grpc_server
from cap_inspector import CapInspector
from x_logger import XLogger

GRPC_OPTIONS = (
    ("grpc.max_send_message_length", 16 * 1024 * 1024),
    ("grpc.max_receive_message_length", 16 * 1024 * 1024),
)

logger = XLogger()
cap = CapInspector(camera_id=0, logger=logger)
server = create_grpc_server(
    ctrl_obj=cap,
    stream_obj=cap,
    grpc_options=GRPC_OPTIONS,
    logger=logger,
)
server.add_insecure_port("0.0.0.0:50051")
server.start()
print("CapInspector server: 0.0.0.0:50051")
try:
    server.wait_for_termination()
finally:
    cap.release()
