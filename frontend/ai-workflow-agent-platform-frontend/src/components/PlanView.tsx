import type { PlanStep, WorkflowStep } from '../types/workflow';

type PlanViewProps = {
  plan: PlanStep[];
  steps: WorkflowStep[];
  emptyMessage?: string;
};

export default function PlanView({ plan, steps, emptyMessage }: PlanViewProps) {
  return (
    <section className="section-card">
      <div className="section-card__header">
        <div>
          <p className="section-card__eyebrow">Planner</p>
          <h3 className="section-card__title">Step timeline</h3>
        </div>

        <p className="section-card__meta">
          {plan.length > 0 ? `${plan.length} planned steps` : 'No plan yet'}
        </p>
      </div>

      {plan.length === 0 ? (
        <div className="empty-state">
          {emptyMessage ??
            'Submit a request to see the planner outline a step-by-step workflow.'}
        </div>
      ) : (
        <div className="timeline">
          {plan.map((step, index) => {
            const runtimeStep = steps.find((item) => item.step === step.step);
            const state = runtimeStep
              ? runtimeStep.status === 'done'
                ? 'done'
                : 'active'
              : 'pending';
            const stateLabel =
              state === 'done'
                ? 'Completed'
                : state === 'active'
                  ? 'In progress'
                  : 'Queued';

            return (
              <article
                key={step.step}
                className={`timeline-item timeline-item--${state}`}
                style={{ animationDelay: `${index * 80}ms` }}
              >
                <div className="timeline-item__track" aria-hidden="true">
                  <span className="timeline-item__dot" />
                  {index < plan.length - 1 && (
                    <span className="timeline-item__line" />
                  )}
                </div>

                <div className="timeline-card">
                  <p className="timeline-card__label">
                    Step {step.step} - {stateLabel}
                  </p>
                  <h4 className="timeline-card__title">{step.description}</h4>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
