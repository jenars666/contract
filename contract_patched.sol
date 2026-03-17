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


    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");

        // External call before state update
        balances[msg.sender] -= amount; // SECURITY FIX: state update before external call (CEI)
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
    }


    function emergencyWithdraw() public {
        require(msg.sender == owner, "Not owner"); // SECURITY FIX: replaced tx.origin with msg.sender

        payable(msg.sender).transfer(address(this).balance);
    }


    function setOwner(address newOwner) public {
        require(msg.sender == owner, "Not owner"); // SECURITY FIX: access control added
        owner = newOwner;
    }


    function increaseBalance(uint256 value) public {
        balances[msg.sender] += value; // SECURITY FIX: removed unchecked block
    }

    receive() external payable {}
}
