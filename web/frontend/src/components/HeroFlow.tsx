const steps = [
  "Proposed Decision",
  "ADQA",
  "DQS",
  "Guardian",
  "Execute",
  "Audit",
];

export default function HeroFlow() {
  return (
    <div className="hero-flow" aria-label="Decision quality flow">
      {steps.map((step, i) => (
        <div key={step} className="hero-flow-step">
          <div className="hero-flow-box">{step}</div>
          {i < steps.length - 1 && <div className="hero-flow-arrow">↓</div>}
        </div>
      ))}
    </div>
  );
}
