import asyncio

import typer
from httpx import AsyncClient

from utils.client import AppClient, SendRequest, get_rpc_uri
from utils.user_op import UserOp

cli = typer.Typer()


@cli.command(help="Send the UserOp to the mempool")
def send_user_op(
    host: str = typer.Argument(..., help="Mempool RPC URL"),
    entry_point: str = typer.Argument(..., help="The entry point address"),
    sender: str = typer.Argument(..., help="The account making the operation"),
    nonce: int = typer.Argument(
        ...,
        help="Anti-replay parameter; also used as the salt for first-time "
        "account creation",
    ),
    init_code: str = typer.Argument(
        ...,
        help="The initCode of the account (needed if and only if the account "
        "is not yet on-chain and needs to be created)",
    ),
    call_data: str = typer.Argument(
        ...,
        help="The data to pass to the sender during the main execution call",
    ),
    call_gas_limit: int = typer.Argument(
        ..., help="The amount of gas to allocate the main execution call"
    ),
    verification_gas_limit: int = typer.Argument(
        ..., help="The amount of gas to allocate for the verification step"
    ),
    pre_verification_gas: int = typer.Argument(
        ...,
        help="The amount of gas to pay for to compensate the bundler for "
        "pre-verification execution and calldata",
    ),
    max_fee_per_gas: int = typer.Argument(
        ..., help="Maximum fee per gas (similar to EIP-1559 max_fee_per_gas)"
    ),
    max_priority_fee_per_gas: int = typer.Argument(
        ...,
        help="Maximum priority fee per gas "
        "(similar to EIP-1559 max_priority_fee_per_gas)",
    ),
    paymaster_and_data: str = typer.Argument(
        ...,
        help="Address of paymaster sponsoring the transaction, followed by "
        "extra data to send to the paymaster (empty for self-sponsored "
        "transaction)",
    ),
    signature: str = typer.Argument(
        ...,
        help="Data passed into the account along with the nonce during the "
        "verification step",
    ),
):
    response = asyncio.run(
        _send_user_op(
            host,
            entry_point,
            sender,
            nonce,
            init_code,
            call_data,
            call_gas_limit,
            verification_gas_limit,
            pre_verification_gas,
            max_fee_per_gas,
            max_priority_fee_per_gas,
            paymaster_and_data,
            signature,
        )
    )
    print(response)


async def _send_user_op(
    host,
    entry_point,
    sender,
    nonce,
    init_code,
    call_data,
    call_gas_limit,
    verification_gas_limit,
    pre_verification_gas,
    max_fee_per_gas,
    max_priority_fee_per_gas,
    paymaster_and_data,
    signature,
):
    async with AsyncClient(base_url=get_rpc_uri(host)) as client:
        user_op = UserOp(
            sender=sender,
            nonce=nonce,
            init_code=init_code,
            call_data=call_data,
            call_gas_limit=call_gas_limit,
            verification_gas_limit=verification_gas_limit,
            pre_verification_gas=pre_verification_gas,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            paymaster_and_data=paymaster_and_data,
            signature=signature,
        )
        send_request = SendRequest(
            entry_point_address=entry_point, user_op=user_op
        )
        return await AppClient(client).send_user_op(send_request.json())


@cli.command(help="Estimate gas parameters for the UserOp")
def estimate_user_op(
    host: str = typer.Argument(..., help="Mempool RPC URL"),
    entry_point: str = typer.Argument(..., help="The entry point address"),
    sender: str = typer.Argument(..., help="The account making the operation"),
    nonce: int = typer.Argument(
        ...,
        help="Anti-replay parameter; also used as the salt for first-time "
        "account creation",
    ),
    init_code: str = typer.Argument(
        ...,
        help="The initCode of the account (needed if and only if the account "
        "is not yet on-chain and needs to be created)",
    ),
    call_data: str = typer.Argument(
        ...,
        help="The data to pass to the sender during the main execution call",
    ),
    call_gas_limit: int = typer.Argument(
        0, help="The amount of gas to allocate the main execution call"
    ),
    verification_gas_limit: int = typer.Argument(
        0, help="The amount of gas to allocate for the verification step"
    ),
    pre_verification_gas: int = typer.Argument(
        0,
        help="The amount of gas to pay for to compensate the bundler for "
        "pre-verification execution and calldata",
    ),
    max_fee_per_gas: int = typer.Argument(
        0, help="Maximum fee per gas (similar to EIP-1559 max_fee_per_gas)"
    ),
    max_priority_fee_per_gas: int = typer.Argument(
        0,
        help="Maximum priority fee per gas "
        "(similar to EIP-1559 max_priority_fee_per_gas)",
    ),
    paymaster_and_data: str = typer.Argument(
        "0x0",
        help="Address of paymaster sponsoring the transaction, followed by "
        "extra data to send to the paymaster (empty for self-sponsored "
        "transaction)",
    ),
    signature: str = typer.Argument(
        ...,
        help="Data passed into the account along with the nonce during the"
        "verification step",
    ),
):
    response = asyncio.run(
        _estimate_user_op(
            host,
            entry_point,
            sender,
            nonce,
            init_code,
            call_data,
            call_gas_limit,
            verification_gas_limit,
            pre_verification_gas,
            max_fee_per_gas,
            max_priority_fee_per_gas,
            paymaster_and_data,
            signature,
        )
    )
    print(response)


async def _estimate_user_op(
    host,
    entry_point,
    sender,
    nonce,
    init_code,
    call_data,
    call_gas_limit,
    verification_gas_limit,
    pre_verification_gas,
    max_fee_per_gas,
    max_priority_fee_per_gas,
    paymaster_and_data,
    signature,
):
    async with AsyncClient(base_url=get_rpc_uri(host)) as client:
        user_op = UserOp(
            sender=sender,
            nonce=nonce,
            init_code=init_code,
            call_data=call_data,
            call_gas_limit=call_gas_limit,
            verification_gas_limit=verification_gas_limit,
            pre_verification_gas=pre_verification_gas,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            paymaster_and_data=paymaster_and_data,
            signature=signature,
        )
        send_request = SendRequest(
            entry_point_address=entry_point, user_op=user_op
        )
        return await AppClient(client).estimate_user_op(send_request.json())


@cli.command(help="Get a UserOp by its hash")
def get_user_op(
    host: str = typer.Argument(..., help="Mempool RPC URL"),
    hash_: str = typer.Argument(..., help="Hash of the UserOp"),
):
    """
    Get a UserOp by its hash
    """
    response = asyncio.run(_get_user_op(host, hash_))
    print(response)


async def _get_user_op(host, hash_):
    async with AsyncClient(base_url=get_rpc_uri(host)) as client:
        return await AppClient(client).get_user_op(hash_)


@cli.command(help="Get a UserOp receipt by its hash")
def get_user_op_receipt(
    host: str = typer.Argument(..., help="Mempool RPC URL"),
    hash_: str = typer.Argument(..., help="Hash of the UserOp"),
):
    """
    Get a UserOp receipt by its hash
    """
    response = asyncio.run(_get_user_op_receipt(host, hash_))
    print(response)


async def _get_user_op_receipt(host, hash_):
    async with AsyncClient(base_url=get_rpc_uri(host)) as client:
        return await AppClient(client).get_user_op_receipt(hash_)


@cli.command(help="Get a list of supported entry points")
def supported_entry_points(
    host: str = typer.Argument(..., help="Mempool RPC URL")
):
    """
    Get a list supported entry points
    """
    response = asyncio.run(_supported_entry_points(host))
    print(response)


async def _supported_entry_points(host):
    async with AsyncClient(base_url=get_rpc_uri(host)) as client:
        return await AppClient(client).supported_entry_points()


@cli.command(help="Get last user operations")
def last_user_ops(host: str = typer.Argument(..., help="Mempool RPC URL")):
    """
    Get a list of last user operations
    """
    response = asyncio.run(_last_user_ops(host))
    print(response)


async def _last_user_ops(host):
    async with AsyncClient(base_url=get_rpc_uri(host)) as client:
        return await AppClient(client).last_user_ops()


if __name__ == "__main__":
    cli()
