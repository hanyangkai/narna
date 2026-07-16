const steps = [
  "Developer",
  "NARNA SDK",
  "Agent",
  "Model",
  "Action",
  "Evidence",
  "Trust",
];

export default function HeroFlow() {
  return (
    <div className="hero-flow" aria-label="Execution flow">
      {steps.map((step, i) => (
        <div key={step} className="hero-flow-step">
          <div className="hero-flow-box">{step}</div>
          {i < steps.length - 1 && <div className="hero-flow-arrow">↓</div>}
        </div>
      ))}
    </div>
  );
}
