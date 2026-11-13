#!/usr/bin/env python
"""grpc_frame の既存 API で CapInspectorClient の .pyi を生成する。"""

from pathlib import Path

import grpc_frame
from grpc_frame.make_pyi import generate_client_pyi


def main() -> None:
    server_grpc_dir = Path(__file__).resolve().parent
    package_dir = server_grpc_dir.parent
    grpc_frame_dir = Path(grpc_frame.__file__).resolve().parent

    generate_client_pyi(
        client_py=server_grpc_dir / "client.py",
        client_class="CapInspectorClient",
        ctrl_py=package_dir / "cap_inspector.py",
        ctrl_class="CapInspector",
        base_py=grpc_frame_dir / "grpc_client.py",
        base_class="GrpcClient",
        out_path=server_grpc_dir / "client.pyi",
    )


if __name__ == "__main__":
    main()
