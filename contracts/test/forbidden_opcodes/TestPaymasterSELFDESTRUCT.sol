// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.12;

import "../../core/BasePaymaster.sol";

/**
 * @title Test paymaster with _validatePaymasterUserOp using the 'SELFDESTRUCT' opcode.
 */
contract TestPaymasterSELFDESTRUCT is BasePaymaster {
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
        address selfDestructor = address(
            bytes20(userOp.paymasterAndData[20:40])
        );
        selfDestructor.call("");
        return ("", 1);
    }
}

contract SelfDestructor {
    fallback() external payable {
        selfdestruct(payable(msg.sender));
    }
}
