from mempool.__main__ import MemPoolService
from protobufs import mempool_pb2

service = MemPoolService()

user_op = mempool_pb2.UserOp(
    sender=b"12345",
    nonce=b"12345",
    init_code=b"12345",
    call_data=b"12345",
    call_gas_limit=b"12345",
    verification_gas_limit=b"12345",
    pre_verification_gas=b"12345",
    max_fee_per_gas=b"12345",
    max_priority_fee_per_gas=b"12345",
    paymaster_and_data=b"12345",
    signature=b"12345"
)

response = service.Add(user_op, None)
print(response)