export default function ProgressStepper({ currentStep }) {
  const steps = [
    { id: 1, label: "Start", icon: "🚀" },
    { id: 2, label: "Analyze", icon: "🔍" },
    { id: 3, label: "Patch", icon: "🔧" },
    { id: 4, label: "Auto-Validate", icon: "✓" },
    { id: 5, label: "Result", icon: "✅" },
    { id: 6, label: "Git Push", icon: "📤" }
  ];

  return (
    <div className="progress-stepper">
      {steps.map((step, index) => (
        <div key={step.id} className="step-wrapper">
          <div className={`step ${currentStep >= step.id ? "active" : ""} ${currentStep > step.id ? "completed" : ""}`}>
            <div className="step-circle">
              {currentStep > step.id ? "✓" : step.icon}
            </div>
            <span className="step-label">{step.label}</span>
          </div>
          {index < steps.length - 1 && (
            <div className={`step-line ${currentStep > step.id ? "completed" : ""}`} />
          )}
        </div>
      ))}
    </div>
  );
}
