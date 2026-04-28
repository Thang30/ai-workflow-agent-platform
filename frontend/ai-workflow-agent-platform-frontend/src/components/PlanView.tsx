export default function PlanView({ plan }: any) {
  return (
    <div>
      <h2>Plan</h2>
      <ul>
        {plan.map((step: any) => (
          <li key={step.step}>
            {step.step}. {step.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
