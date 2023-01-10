from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AddResponse(_message.Message):
    __slots__ = ["userop_id"]
    USEROP_ID_FIELD_NUMBER: _ClassVar[int]
    userop_id: int
    def __init__(self, userop_id: _Optional[int] = ...) -> None: ...

class GetRequest(_message.Message):
    __slots__ = ["to"]
    FROM_FIELD_NUMBER: _ClassVar[int]
    TO_FIELD_NUMBER: _ClassVar[int]
    to: str
    def __init__(self, to: _Optional[str] = ..., **kwargs) -> None: ...

class GetResponse(_message.Message):
    __slots__ = ["userOps"]
    USEROPS_FIELD_NUMBER: _ClassVar[int]
    userOps: _containers.RepeatedCompositeFieldContainer[UserOp]
    def __init__(self, userOps: _Optional[_Iterable[_Union[UserOp, _Mapping]]] = ...) -> None: ...

class UserOp(_message.Message):
    __slots__ = ["call_data", "call_gas_limit", "init_code", "max_fee_per_gas", "max_priority_fee_per_gas", "nonce", "paymaster_and_data", "pre_verification_gas", "sender", "signature", "verification_gas_limit"]
    CALL_DATA_FIELD_NUMBER: _ClassVar[int]
    CALL_GAS_LIMIT_FIELD_NUMBER: _ClassVar[int]
    INIT_CODE_FIELD_NUMBER: _ClassVar[int]
    MAX_FEE_PER_GAS_FIELD_NUMBER: _ClassVar[int]
    MAX_PRIORITY_FEE_PER_GAS_FIELD_NUMBER: _ClassVar[int]
    NONCE_FIELD_NUMBER: _ClassVar[int]
    PAYMASTER_AND_DATA_FIELD_NUMBER: _ClassVar[int]
    PRE_VERIFICATION_GAS_FIELD_NUMBER: _ClassVar[int]
    SENDER_FIELD_NUMBER: _ClassVar[int]
    SIGNATURE_FIELD_NUMBER: _ClassVar[int]
    VERIFICATION_GAS_LIMIT_FIELD_NUMBER: _ClassVar[int]
    call_data: bytes
    call_gas_limit: bytes
    init_code: bytes
    max_fee_per_gas: bytes
    max_priority_fee_per_gas: bytes
    nonce: bytes
    paymaster_and_data: bytes
    pre_verification_gas: bytes
    sender: bytes
    signature: bytes
    verification_gas_limit: bytes
    def __init__(self, sender: _Optional[bytes] = ..., nonce: _Optional[bytes] = ..., init_code: _Optional[bytes] = ..., call_data: _Optional[bytes] = ..., call_gas_limit: _Optional[bytes] = ..., verification_gas_limit: _Optional[bytes] = ..., pre_verification_gas: _Optional[bytes] = ..., max_fee_per_gas: _Optional[bytes] = ..., max_priority_fee_per_gas: _Optional[bytes] = ..., paymaster_and_data: _Optional[bytes] = ..., signature: _Optional[bytes] = ...) -> None: ...
