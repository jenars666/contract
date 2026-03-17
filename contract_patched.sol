pragma solidity ^0.8.0;

contract PaymentVault {

    address public owner;
    mapping(address => uint256) public balances;

    constructor() {
        owner = msg.sender;
    }

    // Deposit funds into vault
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    // ❌ Vulnerable withdraw (Reentrancy)
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // External call before state update
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        balances[msg.sender] -= amount;
    }

    // ❌ tx.origin vulnerability
    function emergencyWithdraw() public {
        require(tx.origin == owner, "Not owner");

        payable(msg.sender).transfer(address(this).balance);
    }

    // ❌ Missing access control
    function setOwner(address newOwner) public {
        owner = newOwner;
    }

    // ❌ Unsafe arithmetic (simulated logic bug)
    function increaseBalance(uint256 value) public {
        unchecked {
            balances[msg.sender] += value;
        }
    }

    receive() external payable {}
}