from urllib.parse import urlparse, urlunparse

from httpx import AsyncClient

from utils.user_op import UserOp


class AppClient:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def send_user_op(self, request: dict, **kwargs) -> str:
        return await self._make_request(
            "eth_sendUserOperation", json=request, **kwargs
        )

    async def estimate_user_op(self, request: dict, **kwargs) -> dict:
        return await self._make_request(
            "eth_estimateUserOperationGas", json=request, **kwargs
        )

    async def get_user_op(self, hash_: str, **kwargs) -> dict:
        return await self._make_request(
            "eth_getUserOperationByHash", json={"hash": hash_}, **kwargs
        )

    async def get_user_op_receipt(self, hash_: str, **kwargs) -> dict:
        return await self._make_request(
            "eth_getUserOperationReceipt", json={"hash": hash_}, **kwargs
        )

    async def supported_entry_points(self, **kwargs) -> dict:
        return await self._make_request(
            "eth_supportedEntryPoints", json={}, **kwargs
        )

    async def last_user_ops(self, **kwargs) -> dict:
        return await self._make_request(
            "eth_lastUserOperations", json={}, **kwargs
        )

    async def _make_request(self, method: str, json: dict):
        response = await self.client.post(method, json=json)
        return response.json()


class SendRequest:
    def __init__(self, entry_point_address: str, user_op: UserOp):
        self.entry_point = entry_point_address
        self.user_op = user_op

    def json(self):
        return {
            "user_op": {
                k: self._to_hex(v) for k, v in self.user_op.dict().items()
            },
            "entry_point": self.entry_point,
        }

    @classmethod
    def _to_hex(cls, v) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, int):
            return hex(v)
        if isinstance(v, bytes):
            return "0x" + bytes.hex(v)


def get_rpc_uri(uri: str, port: int = 8545) -> str:
    parsed = urlparse(uri)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid URI")

    host = parsed.netloc.split(":")[0]
    return urlunparse(
        (
            parsed.scheme,
            f"{host}:{port}",
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
