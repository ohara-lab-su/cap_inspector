from cap_inspector import CapInspectorClient

client = CapInspectorClient("127.0.0.1", 50051)
print(client.get_parameters())
print(client.get_status())
client.close()
