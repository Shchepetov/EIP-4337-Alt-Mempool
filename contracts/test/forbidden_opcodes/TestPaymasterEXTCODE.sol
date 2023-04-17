// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.12;

import "../../core/BasePaymaster.sol";

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'EXTCODEHASH' opcode.
 */
contract TestPaymasterEXTCODEHASH is BasePaymaster {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    )
        internal
        view
        virtual
        override
        returns (bytes memory context, uint256 validationData)
    {
        address addr = address(bytes20(userOp.paymasterAndData[20:40]));
        bytes32 codeHash;
        assembly {
            codeHash := extcodehash(addr)
        }
        return ("", uint256(codeHash) > 0 ? 1 : 0);
    }
}

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'EXTCODESIZE' opcode.
 */
contract TestPaymasterEXTCODESIZE is BasePaymaster {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    )
        internal
        view
        virtual
        override
        returns (bytes memory context, uint256 validationData)
    {
        address addr = address(bytes20(userOp.paymasterAndData[20:40]));
        uint256 codeSize;
        assembly {
             codeSize := extcodesize(addr)
        }
        return ("", codeSize > 0 ? 1 : 0);
    }
}

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'EXTCODECOPY' opcode.
 */
contract TestPaymasterEXTCODECOPY is BasePaymaster {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _validatePaymasterUserOp(
        UserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    )
        internal
        view
        virtual
        override
        returns (bytes memory context, uint256 validationData)
    {
        address addr = address(bytes20(userOp.paymasterAndData[20:40]));
        assembly {
            extcodecopy(addr, 0, 0, 0)
        }
        return ("", 1);
    }
}