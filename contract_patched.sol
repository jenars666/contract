pragma solidity ^0.8.0;

contract VulnerableBank {

    mapping(address => uint) public balances;

    // Deposit funds
    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() public {
        uint amount = balances[msg.sender];

        require(amount > 0, "No balance");

        // External call BEFORE state update → VULNERABLE
        (bool success,) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");

        // State update AFTER transfer → BAD
        balances[msg.sender] = 0;
    }
}
