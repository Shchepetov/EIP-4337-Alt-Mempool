// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.12;

import "../../core/BasePaymaster.sol";

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode before `CALL` opcode.
 */
contract TestPaymasterGASBeforeCALL is BasePaymaster {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    )
        internal
        virtual
        override
        returns (bytes memory context, uint256 validationData)
    {
        address callee = address(bytes20(userOp.paymasterAndData[20:40]));
        callee.call("");
    }
}

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode before `DELEGATECALL` opcode.
 */
contract TestPaymasterGASBeforeDELEGATECALL is BasePaymaster {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    )
        internal
        virtual
        override
        returns (bytes memory context, uint256 validationData)
    {
        address callee = address(bytes20(userOp.paymasterAndData[20:40]));
        callee.delegatecall("");
    }
}

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode before `STATICCALL` opcode.
 */
contract TestPaymasterGASBeforeSTATICCALL is BasePaymaster {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    )
        internal
        virtual
        override
        returns (bytes memory context, uint256 validationData)
    {
        address callee = address(bytes20(userOp.paymasterAndData[20:40]));
        callee.staticcall("");
    }
}
