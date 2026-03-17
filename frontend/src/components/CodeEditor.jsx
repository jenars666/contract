import Editor from "@monaco-editor/react";

const REENTRANCY_DEMO = `// SPDX-License-Identifier: MIT
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

    function migrate(address user, uint256 amount) external {
        require(msg.sender == admin, "only admin");
        balances[user] += amount;
    }

    function getBalance(address user) external view returns (uint256) {
        return balances[user];
    }

    receive() external payable {}
}`;

const OVERFLOW_DEMO = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableToken {
    string public name = "HackMatrix Demo Token";
    string public symbol = "HDT";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    mapping(address => uint256) private balances;
    mapping(address => mapping(address => uint256)) public allowances;

    event Transfer(address indexed from, address indexed to, uint256 amount);
    event Approval(address indexed owner, address indexed spender, uint256 amount);

    constructor(uint256 supply) {
        totalSupply = supply;
        balances[msg.sender] = supply;
    }

    function balanceOf(address user) external view returns (uint256) {
        return balances[user];
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(to != address(0), "bad recipient");
        unchecked {
            balances[msg.sender] = balances[msg.sender] - amount;
            balances[to] = balances[to] + amount;
        }
        emit Transfer(msg.sender, to, amount);
        return true;
    }

    function approve(address spender, uint256 amount) external returns (bool) {
        allowances[msg.sender][spender] = amount;
        emit Approval(msg.sender, spender, amount);
        return true;
    }

    function transferFrom(address from, address to, uint256 amount) external returns (bool) {
        uint256 allowed = allowances[from][msg.sender];
        require(allowed >= amount, "allowance low");
        allowances[from][msg.sender] = allowed - amount;
        unchecked {
            balances[from] = balances[from] - amount;
            balances[to] = balances[to] + amount;
        }
        emit Transfer(from, to, amount);
        return true;
    }

    function mint(address to, uint256 amount) external {
        unchecked {
            totalSupply += amount;
            balances[to] += amount;
        }
        emit Transfer(address(0), to, amount);
    }
}`;

const TXORIGIN_DEMO = `// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VulnerableWallet {
    address public owner;

    event Deposited(address indexed from, uint256 amount);
    event Withdrawn(address indexed to, uint256 amount);
    event OwnershipTransferred(address indexed oldOwner, address indexed newOwner);

    constructor() payable {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(tx.origin == owner, "only owner");
        _;
    }

    function deposit() external payable {
        require(msg.value > 0, "empty deposit");
        emit Deposited(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) external onlyOwner {
        require(amount <= address(this).balance, "low balance");
        (bool ok, ) = payable(msg.sender).call{value: amount}("");
        require(ok, "withdraw failed");
        emit Withdrawn(msg.sender, amount);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "zero owner");
        emit OwnershipTransferred(owner, newOwner);
        owner = newOwner;
    }

    function getOwner() external view returns (address) {
        return owner;
    }

    receive() external payable {}
}`;

export default function CodeEditor({ code, onChange, isAnalyzing, onAnalyze }) {
  const lineCount = code ? code.split("\n").length : 0;

  return (
    <section className="card">
      <div className="section-title-row">
        <h2>Solidity Contract Input</h2>
        <div className="demo-buttons">
          <button className="btn-ghost red" onClick={() => onChange(REENTRANCY_DEMO)}>
            Reentrancy Bug
          </button>
          <button className="btn-ghost amber" onClick={() => onChange(OVERFLOW_DEMO)}>
            Integer Overflow
          </button>
          <button className="btn-ghost blue" onClick={() => onChange(TXORIGIN_DEMO)}>
            tx.origin Auth
          </button>
        </div>
      </div>

      <Editor
        language="sol"
        theme="vs-dark"
        height="420px"
        value={code}
        onChange={(value) => onChange(value || "")}
        options={{
          fontSize: 13,
          minimap: { enabled: false },
          wordWrap: "on",
          lineNumbers: "on",
          scrollBeyondLastLine: false,
        }}
      />

      <div className="editor-footer">
        <div>
          {code.length} characters | {lineCount} lines
        </div>
        <button className="btn-primary" disabled={!code.trim() || isAnalyzing} onClick={onAnalyze}>
          {isAnalyzing ? (
            <>
              <span className="spinner" /> Analyzing...
            </>
          ) : (
            "Analyze Contract"
          )}
        </button>
      </div>
    </section>
  );
}
