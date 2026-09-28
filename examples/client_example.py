from grpc_frame.grpc_client import GrpcClient

client = GrpcClient("127.0.0.1", 50051)
print(client.get_parameters())
print(client.get_status())
client.close()
