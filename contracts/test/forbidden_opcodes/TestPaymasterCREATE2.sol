// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.12;

import "../../core/BasePaymaster.sol";
import "../TestCounter.sol";

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'CREATE2' opcode.
 */
contract TestPaymasterCREATE2 is BasePaymaster {
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
        TestCounter testCounter = new TestCounter{salt: bytes32("")}();
        return ("", 1);
    }
}
