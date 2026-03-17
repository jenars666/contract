// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableToken {
    string public name = "Vulnerable Token";
    string public symbol = "VUL";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) private balances;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    constructor(uint256 initialSupply) {
        totalSupply = initialSupply;
        balances[msg.sender] = initialSupply;
        emit Transfer(address(0), msg.sender, initialSupply);
    }

    function balanceOf(address account) public view returns (uint256) {
        return balances[account];
    }

    function transfer(address to, uint256 amount) public returns (bool) {
        require(to != address(0), "zero address");

        // INTENTIONAL BUG: unchecked subtraction can underflow.
        unchecked {
            balances[msg.sender] = balances[msg.sender] - amount;
            balances[to] = balances[to] + amount;
        }

        emit Transfer(msg.sender, to, amount);
        return true;
    }

    function approve(address spender, uint256 amount) public returns (bool) {
        require(spender != address(0), "zero spender");
        allowance[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) public returns (bool) {
        require(to != address(0), "zero address");
        uint256 allowed = allowance[from][msg.sender];
        require(allowed >= amount, "insufficient allowance");

        allowance[from][msg.sender] = allowed - amount;

        // INTENTIONAL BUG: unchecked arithmetic still used here.
        unchecked {
            balances[from] = balances[from] - amount;
            balances[to] = balances[to] + amount;
        }

        emit Transfer(from, to, amount);
        return true;
    }

    function mint(address to, uint256 amount) public returns (bool) {
        require(to != address(0), "zero address");

        unchecked {
            totalSupply += amount;
            balances[to] += amount;
        }

        emit Transfer(address(0), to, amount);
        return true;
    }
}
