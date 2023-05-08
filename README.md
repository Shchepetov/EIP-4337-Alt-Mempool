# EIP-4337 Alt Mempool

This project implements the RPC service based on the protocol described in
[EIP-4337](https://eips.ethereum.org/EIPS/eip-4337), with several 
distinctive features that set it apart from the original workflow:

⛓️ **White list of auxiliary smart contract bytecodes** - UserOps using Factory,
Account or Paymaster, whose bytecode is on the white list are added to the
mempool without checking the opcodes used during simulation. Smart contract
bytecode can be manually added to the white list by the pool administrator
using a special command.

⛓️ **Black list of auxiliary smart contract bytecodes** - UserOps using Factory,
Account, or Paymaster, whose bytecode is on the blacklist, are rejected.
Smart contract bytecode can be added to the blacklist manually using a
special command or the bytecode is added automatically during UserOp
verification when added to the mempool. When a bytecode is added to the
blacklist, any UserOps using that bytecode which have already been added to
the mempool will be removed.

⛓️ **Zero tolerance** - Within the pool, only one UserOp that uses the same
bytecode, not on the white list, can be present simultaneously. The stake
check described in EIP-4337 is not performed at the same time.

### Supported methods:
- `eth_sendUserOperation`
- `eth_estimateUserOperationGas`
- `eth_getUserOperationByHash`
- `eth_getUserOperationReceipt`
- `eth_supportedEntryPoints`
- `eth_lastUserOperations`

## Try out the implemented mempool on the Gnosis
You can use the mempool with the entry point located at 
http://shchepetov.xyz/api/:
- Network: **[Gnosis](https://www.gnosis.io)**
- UserOp lifetime: **30 minutes**
- maxVerificationGasLimit: **200 000**
- Minimum maxFeePerGas: **1** Gwei
- Minimum maxPriorityFeePerGas: **1** Gwei
- Allowed EntryPoints: **[0xf5bF2a0441E28034B03B642C19787BB505c5fFc1](https://gnosisscan.io/address/0xf5bF2a0441E28034B03B642C19787BB505c5fFc1)**  
- Whitelisted Factory contracts byte-code: **[SimpleAcountFactory](https://gnosisscan.io/address/0xc51Bd464939c4309E54Ec185Ad0c54B951BE649F)**  
- Whitelisted Paymaster contracts byte-code: **[DepositPaymaster](https://gnosisscan.io/address/0xabAD2F5cB4ae44E158405292b43338ebF0d22214)**

The repository contains a simple client application `./client.py` for convenient
use of the remote mempool, which allows you to call all supported mempool 
methods.  
_To learn more about how to call these methods on the remote mempool, run the 
following command: `python3 client.py --help`._


## Run your own mempool
### Prerequisites

```shell
apt-get update && apt-get install -y sudo gnupg2 software-properties-common nodejs npm postgresql postgresql-contrib gcc python3-dev python3-pip
```

```shell
npm install -g ganache-cli && npm install -g solc
```
```shell
python3 -m pip install -r requirements.txt
```
This project uses the [Brownie](https://eth-brownie.readthedocs.io/en/stable/)
framework for testing and generating ABI of smart contracts. Before beginning
work, you need to install the necessary packages and compile the smart contracts:

```shell
brownie pm install OpenZeppelin/openzeppelin-contracts@4.8.2 && brownie pm install safe-global/safe-contracts@1.3.0
```
```shell
rm -r build/contracts/*.json && brownie compile
```
### Initialize database
1. Run the PostgreSQL service:
```shell
service postgresql start && sudo -u postgres createdb mydb
```
2. Set the following environment variables:
- `DB_HOST` (default is `localhost`)
- `DB_USER`
- `DB_PASSWORD`
3. Initialize databases:
```shell
python3 manage.py initialize-db
```
### Run the RPC server

1. Set the `RPC_ENDPOINT_URI` environment variable to the external entry point
of the RPC API node.  
> ⚠️ The node must support the `debug_traceCall` method.
2. Run the mempool service
```shell
python3 manage.py runserver --workers=%NUMBER_OF_WORKERS%
```
_To get additional information about mempool administration capabilities,
execute the following command: ```python3 manage.py --help```_

