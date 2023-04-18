// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.12;

import "../../core/BasePaymaster.sol";

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'CALL' opcode.
 */
contract TestPaymasterCALL is BasePaymaster {
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
 * @title Test paymaster with _validatePaymasterUserOp using the 'CALLCODE' opcode.
 */
contract TestPaymasterCALLCODE is BasePaymaster {
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
        try this.callCode(callee) {}
            catch (bytes memory data) {
                return ("", 1);
            }
    }

    function callCode(address callee) external returns (uint256 validationData) {
        assembly {
            validationData := callcode(callee, 0,0,0,0,0,0)
        }
    }
}

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'DELEGATECALL' opcode.
 */
contract TestPaymasterDELEGATECALL is BasePaymaster {
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
        assembly {
            validationData := delegatecall(callee, 0, 0, 0, 0, 0)
        }
    }
}

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'STATICCALL' opcode.
 */
contract TestPaymasterSTATICCALL is BasePaymaster {
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
        assembly {
            validationData := staticcall(callee, 0, 0, 0, 0, 0)
        }
    }
}
