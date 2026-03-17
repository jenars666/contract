// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableWallet {
    address public owner;

    event Deposited(address indexed sender, uint256 value);
    event Withdrawn(address indexed recipient, uint256 value);
    event OwnerChanged(address indexed oldOwner, address indexed newOwner);

    constructor() payable {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        // INTENTIONAL BUG: tx.origin used for authorization.
        require(tx.origin == owner, "only owner");
        _;
    }

    function deposit() external payable {
        require(msg.value > 0, "empty deposit");
        emit Deposited(msg.sender, msg.value);
    }

    function withdraw(address payable recipient, uint256 amount) external onlyOwner {
        require(recipient != address(0), "zero recipient");
        require(amount <= address(this).balance, "insufficient balance");

        (bool sent, ) = recipient.call{value: amount}("");
        require(sent, "withdraw failed");
        emit Withdrawn(recipient, amount);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "zero owner");
        emit OwnerChanged(owner, newOwner);
        owner = newOwner;
    }

    function getOwner() external view returns (address) {
        return owner;
    }

    receive() external payable {
        emit Deposited(msg.sender, msg.value);
    }
}
