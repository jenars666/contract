import React from 'react';

const RiskScore = ({ score }) => {
    let color = '#3fb950'; // Green
    let severity = 'LOW RISK';
    
    if (score >= 70) {
        color = '#f85149'; // Red
        severity = 'CRITICAL RISK';
    } else if (score >= 40) {
        color = '#d29922'; // Amber
        severity = 'MEDIUM RISK';
    }

    const radius = 60;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (score / 100) * circumference;

    return (
        <div className="risk-score-card">
            <h3 style={{ margin: '0 0 15px 0', textAlign: 'center' }}>Contract Risk Score</h3>
            <div className="gauge-container">
                <svg width="150" height="150" className="gauge">
                    <circle 
                        cx="75" cy="75" r={radius} 
                        stroke="#30363d" 
                        strokeWidth="12" 
                        fill="transparent" 
                    />
                    <circle 
                        cx="75" cy="75" r={radius} 
                        stroke={color} 
                        strokeWidth="12" 
                        fill="transparent" 
                        strokeDasharray={circumference}
                        strokeDashoffset={strokeDashoffset}
                        strokeLinecap="round"
                        style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
                    />
                </svg>
                <div className="gauge-text">
                    <span className="score" style={{ color }}>{score}</span>
                    <span className="max">/100</span>
                </div>
            </div>
            <div className="severity-label" style={{ color }}>{severity}</div>
        </div>
    );
};

export default RiskScore;
