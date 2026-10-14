from cap_inspector.server_grpc import CapInspectorClient
from cap_inspector.viewer import run_viewer

# HOST = "10.170.10.55"
HOST = "127.0.0.1"
PORT = 50051


if __name__ == "__main__":
    client = CapInspectorClient(HOST, PORT)
    run_viewer(
        inspector=client,
        close_callback=client.close,
    )
