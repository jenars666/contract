// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title VulnerableBank
/// @notice Demo-only contract intentionally vulnerable to reentrancy.
contract VulnerableBank {
    mapping(address => uint256) public balances;
    address public treasury;
    uint256 public totalDeposits;

    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);

    constructor(address _treasury) {
        require(_treasury != address(0), "invalid treasury");
        treasury = _treasury;
    }

    /// @notice Users can deposit ETH to later withdraw.
    function deposit() external payable {
        require(msg.value > 0, "value must be > 0");
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /// @notice Vulnerable withdraw flow for security testing.
    /// @dev Bug: external call is executed before state updates.
    function withdraw(uint256 amount) external {
        require(amount > 0, "amount must be > 0");
        require(balances[msg.sender] >= amount, "insufficient balance");

        // VULNERABLE: interaction comes before effects.
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "transfer failed");

        // State update happens after interaction.
        balances[msg.sender] -= amount;
        totalDeposits -= amount;
        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Sends protocol fee from contract to treasury.
    function flushFee(uint256 feeAmount) external {
        require(msg.sender == treasury, "only treasury");
        require(feeAmount <= address(this).balance, "insufficient contract balance");
        (bool sent, ) = treasury.call{value: feeAmount}("");
        require(sent, "fee transfer failed");
    }

    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }

    receive() external payable {
        balances[msg.sender] += msg.value;
        totalDeposits += msg.value;
        emit Deposited(msg.sender, msg.value);
    }
}
