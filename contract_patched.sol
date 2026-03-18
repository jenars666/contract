pragma solidity ^0.8.0;
contract Bank {
    mapping(address => uint) public balances;
    function withdraw(uint amount) public {
        if (balances[msg.sender] >= amount) {
            (bool success, ) = msg.sender.call{value: amount}("");
            require(success);
            balances[msg.sender] -= amount;
        }
    }
}
