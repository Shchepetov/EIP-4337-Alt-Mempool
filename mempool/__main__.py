from concurrent import futures

import grpc

from grpc_interceptor import ExceptionToStatusInterceptor

from protobufs import mempool_pb2_grpc
from protobufs import mempool_pb2

from pathlib import Path

class MemPoolService(mempool_pb2_grpc.MemPoolServicer):
    def Add(self, request, context):
        return mempool_pb2.AddResponse(userop_id=1)

    def Get(self, request, context):
        return mempool_pb2.GetResponse([])


def serve():
    interceptors = [ExceptionToStatusInterceptor()]
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), interceptors=interceptors
    )
    mempool_pb2_grpc.add_MemPoolServicer_to_server(
        MemPoolService(), server
    )

    keys_path = Path(__file__).parent / 'keys'
    with open(keys_path / 'server.key', "rb") as fp:
        server_key = fp.read()
    with open(keys_path / 'server.pem', "rb") as fp:
        server_cert = fp.read()
    with open(keys_path / 'ca.pem', "rb") as fp:
        ca_cert = fp.read()

    creds = grpc.ssl_server_credentials(
        [(server_key, server_cert)],
        root_certificates=ca_cert,
        require_client_auth=True,
    )
    server.add_secure_port("[::]:443", creds)
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()