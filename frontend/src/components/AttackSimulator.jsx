import React, { useState, useEffect } from 'react';

const AttackSimulator = ({ type, isPatched }) => {
  const [walletBalance, setWalletBalance] = useState(100);
  const [contractBalance, setContractBalance] = useState(10);
  const [status, setStatus] = useState('IDLE'); // IDLE, ATTACKING, BLOCKED, DRAINED

  useEffect(() => {
    setWalletBalance(100);
    setContractBalance(10);
    setStatus('IDLE');
  }, [type, isPatched]);

  const simulateAttack = () => {
    setStatus('ATTACKING');
    let currentWallet = 100;
    
    if (isPatched) {
      // Simulate blocked attack
      setTimeout(() => {
        setStatus('BLOCKED');
      }, 400); // 400ms interval as requested
      return;
    }

    // Vulnerable animation
    const interval = setInterval(() => {
      currentWallet -= 10;
      if (currentWallet <= 0) {
        currentWallet = 0;
        clearInterval(interval);
        setStatus('DRAINED');
      }
      setWalletBalance(currentWallet);
      setContractBalance(prev => prev + 10);
    }, 400); // 400ms interval
  };

  return (
    <div className="attack-simulator">
      <div className="sim-header">
        <h4>🚨 Live Attack Simulation 🚨</h4>
        <button onClick={simulateAttack} disabled={status === 'ATTACKING'} className="sim-btn">
          {status === 'ATTACKING' ? "Attacking..." : (isPatched ? "Simulate Attack (Patched)" : "Simulate Attack (Vulnerable)")}
        </button>
      </div>
      
      <div className="sim-body">
        <div className="sim-box contract-box">
          <span className="sim-label">Target Contract</span>
          <span className="sim-balance">{walletBalance} ETH</span>
        </div>
        
        <div className="sim-animation-area">
          {status === 'ATTACKING' && <div className="laser-beam"></div>}
          {status === 'BLOCKED' && <div className="shield-block">🛡️ BLOCKED</div>}
          {status === 'DRAINED' && <div className="skull-icon">💀 DRAINED</div>}
        </div>
        
        <div className="sim-box attacker-box">
          <span className="sim-label">Attacker Wallet</span>
          <span className="sim-balance">{contractBalance} ETH</span>
        </div>
      </div>
      
      {status === 'BLOCKED' && (
        <div className="sim-alert success">
          Attack neutralized! State was updated before the transfer, or proper auth was used.
        </div>
      )}
      {status === 'DRAINED' && (
        <div className="sim-alert danger">
          Contract drained in 4 seconds!
        </div>
      )}
    </div>
  );
};

export default AttackSimulator;
