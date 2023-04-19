// SPDX-License-Identifier: GPL-3.0-only
pragma solidity ^0.8.12;

import "../core/BasePaymaster.sol";

/**
 * @dev Test paymaster with _validatePaymasterUserOp using some opcode.
 */
abstract contract TestPaymasterCallOpcode is BasePaymaster {
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
        address context = address(bytes20(userOp.paymasterAndData[20:]));
        _callOpcode(context);
    }

    function _callOpcode(address context) internal virtual {}
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'BALANCE' opcode.
 */
contract TestPaymasterBALANCE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(address(0).balance);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'BLOCKHASH' opcode.
 */
contract TestPaymasterBLOCKHASH is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(blockhash(0));
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CALL' opcode.
 */
contract TestPaymasterCALL is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        context.call("");
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CALLCODE' opcode.
 */
contract TestPaymasterCALLCODE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        uint256 dummy;
        assembly {
            dummy := callcode(123, context, 0, 0, 0, 0, 0)
        }
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'COINBASE' opcode.
 */
contract TestPaymasterCOINBASE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(block.coinbase);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CREATE' opcode.
 */
contract TestPaymasterCREATE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        new SelfDestructor();
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'CREATE2' opcode.
 */
contract TestPaymasterCREATE2 is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        new SelfDestructor{salt: bytes32("")}();
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'DELEGATECALL' opcode.
 */
contract TestPaymasterDELEGATECALL is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        uint256 dummy;
        assembly {
            dummy := delegatecall(123, context, 0, 0, 0, 0)
        }
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'DIFFICULTY' opcode.
 */
contract TestPaymasterDIFFICULTY is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(block.difficulty);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'EXTCODEHASH' opcode.
 */
contract TestPaymasterEXTCODEHASH is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes32 codeHash;
        assembly {
            codeHash := extcodehash(context)
        }
        bytes memory dummy = abi.encodePacked(codeHash);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'EXTCODESIZE' opcode.
 */
contract TestPaymasterEXTCODESIZE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        uint256 codeSize;
        assembly {
            codeSize := extcodesize(context)
        }
        bytes memory dummy = abi.encodePacked(codeSize);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'EXTCODECOPY' opcode.
 */
contract TestPaymasterEXTCODECOPY is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        assembly {
            extcodecopy(context, 0, 0, 0)
        }
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode.
 */
contract TestPaymasterGAS is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(gasleft());
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode before `CALL` opcode.
 */
contract TestPaymasterGASBeforeCALL is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        context.call("");
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode before `CALLCODE` opcode.
 */
contract TestPaymasterGASBeforeCALLCODE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        uint256 dummy;
        assembly {
            dummy := callcode(gas(), context, 0, 0, 0, 0, 0)
        }
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode before `DELEGATECALL` opcode.
 */
contract TestPaymasterGASBeforeDELEGATECALL is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        context.delegatecall("");
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GAS' opcode before `STATICCALL` opcode.
 */
contract TestPaymasterGASBeforeSTATICCALL is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        context.staticcall("");
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GASLIMIT' opcode.
 */
contract TestPaymasterGASLIMIT is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(block.gaslimit);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'GASPRICE' opcode.
 */
contract TestPaymasterGASPRICE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(tx.gasprice);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'NUMBER' opcode.
 */
contract TestPaymasterNUMBER is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(block.number);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'ORIGIN' opcode.
 */
contract TestPaymasterORIGIN is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(tx.origin);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'SELFBALANCE' opcode.
 */
contract TestPaymasterSELFBALANCE is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(address(this).balance);
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'SELFDESTRUCT' opcode.
 */
contract TestPaymasterSELFDESTRUCT is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        context.call("");
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'STATICCALL' opcode.
 */
contract TestPaymasterSTATICCALL is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        uint256 dummy;
        assembly {
            dummy := staticcall(123, context, 0, 0, 0, 0)
        }
    }
}

/**
 * @dev Test paymaster with _validatePaymasterUserOp using the 'TIMESTAMP' opcode.
 */
contract TestPaymasterTIMESTAMP is TestPaymasterCallOpcode {
    constructor(IEntryPoint _entryPoint) BasePaymaster(_entryPoint) {}

    function _callOpcode(address context) internal override {
        bytes memory dummy = abi.encodePacked(block.timestamp);
    }
}

contract SelfDestructor {
    fallback() external payable {
        selfdestruct(payable(msg.sender));
    }
}
