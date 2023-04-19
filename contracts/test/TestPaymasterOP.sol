// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.12;

import "../core/BasePaymaster.sol";

/**
 * @dev Test paymaster with _validatePaymasterUserOp using some opcode.
 */
abstract contract TestPaymasterOP is BasePaymaster {
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
        _callOpcode();
    }

    function _callOpcode() internal virtual {}
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'BALANCE' opcode.
 */
contract TestPaymasterBALANCE is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(address(0).balance);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'BLOCKHASH' opcode.
 */
contract TestPaymasterBLOCKHASH is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(blockhash(0));
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'COINBASE' opcode.
 */
contract TestPaymasterCOINBASE is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(block.coinbase);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CREATE' opcode.
 */
contract TestPaymasterCREATE is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        new SelfDestructor();
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CREATE2' opcode.
 */
contract TestPaymasterCREATE2 is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        new SelfDestructor{salt: bytes32("")}();
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'DIFFICULTY' opcode.
 */
contract TestPaymasterDIFFICULTY is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(block.difficulty);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode.
 */
contract TestPaymasterGAS is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(gasleft());
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GASLIMIT' opcode.
 */
contract TestPaymasterGASLIMIT is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(block.gaslimit);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GASPRICE' opcode.
 */
contract TestPaymasterGASPRICE is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(tx.gasprice);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'NUMBER' opcode.
 */
contract TestPaymasterNUMBER is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(block.number);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'ORIGIN' opcode.
 */
contract TestPaymasterORIGIN is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(tx.origin);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'SELFBALANCE' opcode.
 */
contract TestPaymasterSELFBALANCE is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(address(this).balance);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'TIMESTAMP' opcode.
 */
contract TestPaymasterTIMESTAMP is TestPaymasterOP {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode() internal override {
        bytes memory dummy = abi.encodePacked(block.timestamp);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using EXCTCODE* opcode.
 */
abstract contract TestPaymasterEXTCODE is BasePaymaster {
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
        _callOpcode(address(bytes20(userOp.paymasterAndData[20:40])));
    }

    function _callOpcode(address target) internal virtual {}
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'EXTCODEHASH' opcode.
 */
contract TestPaymasterEXTCODEHASH is TestPaymasterEXTCODE {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address target) internal override {
        bytes32 codeHash;
        assembly {
            codeHash := extcodehash(target)
        }
        bytes memory dummy = abi.encodePacked(codeHash);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'EXTCODESIZE' opcode.
 */
contract TestPaymasterEXTCODESIZE is TestPaymasterEXTCODE {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address target) internal override {
        uint256 codeSize;
        assembly {
            codeSize := extcodesize(target)
        }
        bytes memory dummy = abi.encodePacked(codeSize);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'EXTCODECOPY' opcode.
 */
contract TestPaymasterEXTCODECOPY is TestPaymasterEXTCODE {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address target) internal override {
        assembly {
            extcodecopy(target, 0, 0, 0)
        }
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using CALL* opcode.
 */
abstract contract TestPaymasterCALL_ is BasePaymaster {
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
        _callOpcode(
            address(bytes20(userOp.paymasterAndData[20:40])),
            userOp.paymasterAndData[40:]
        );
    }

    function _callOpcode(address target, bytes memory payload)
        internal
        virtual
    {}
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CALL' opcode.
 */
contract TestPaymasterCALL is TestPaymasterCALL_ {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address target, bytes memory payload)
        internal
        override
    {
        target.call(payload);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CALLCODE' opcode.
 */
contract TestPaymasterCALLCODE is TestPaymasterCALL_ {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address target, bytes memory payload)
        internal
        override
    {
        uint256 dummy;
        assembly {
            let size := mload(payload)
            let ptr := add(payload, 0x20)
            dummy := callcode(123, target, 0, ptr, size, 0, 0)
        }
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'DELEGATECALL' opcode.
 */
contract TestPaymasterDELEGATECALL is TestPaymasterCALL_ {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address target, bytes memory payload)
        internal
        override
    {
        target.delegatecall(payload);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'STATICCALL' opcode.
 */
contract TestPaymasterSTATICCALL is TestPaymasterCALL_ {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address target, bytes memory payload)
        internal
        override
    {
        target.staticcall(payload);
    }
}

contract SelfDestructor {
    fallback() external payable {
        selfdestruct(payable(msg.sender));
    }
}
