// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableBank {
    mapping(address => uint256) public balances;
    address public admin;

    constructor() {
        admin = msg.sender;
    }

    function deposit() external payable {
        require(msg.value > 0, "zero value");
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) external {
        require(amount > 0, "amount is zero");
        require(balances[msg.sender] >= amount, "insufficient balance");

        // VULNERABILITY: external interaction before effects
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok, "transfer failed");

        balances[msg.sender] -= amount;
    }

    receive() external payable {}
}
