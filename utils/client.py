from httpx import AsyncClient


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
        response = await self.client.post(f"/api/{method}", json=json)
        return response.json()
