export default function PlanView({ plan }: any) {
  return (
    <div className="card">
      <h2>🧠 Plan</h2>
      <ul>
        {plan.map((step: any) => (
          <li key={step.step} style={{ marginBottom: '6px' }}>
            <strong>{step.step}.</strong> {step.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
