import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { WorkflowStep } from '../types/workflow';

type TraceViewProps = {
  steps: WorkflowStep[];
};

export default function TraceView({ steps }: TraceViewProps) {
  const completedSteps = steps.filter((step) => step.status === 'done').length;

  return (
    <section className="section-card">
      <div className="section-card__header">
        <div>
          <p className="section-card__eyebrow">Executor</p>
          <h3 className="section-card__title">Execution cards</h3>
        </div>

        <p className="section-card__meta">
          {steps.length > 0
            ? `${completedSteps}/${steps.length} complete`
            : 'Waiting for execution'}
        </p>
      </div>

      {steps.length === 0 ? (
        <div className="empty-state">
          As each planned step starts, it appears here with status, tool usage,
          and expandable output.
        </div>
      ) : (
        <div className="execution-stack">
          {steps.map((step, index) => (
            <article
              key={step.step}
              className={`execution-card execution-card--${step.status}`}
              style={{ animationDelay: `${index * 90}ms` }}
            >
              <div className="execution-card__header">
                <div>
                  <p className="execution-card__eyebrow">Step {step.step}</p>
                  <h4 className="execution-card__title">{step.description}</h4>
                </div>

                <span className={`status-chip status-chip--${step.status}`}>
                  {step.status === 'running' ? 'Running' : 'Done'}
                </span>
              </div>

              {step.tools.length > 0 && (
                <div className="tool-list">
                  <p className="execution-card__subheading">Used tools</p>

                  {step.tools.map((tool, toolIndex) => (
                    <div
                      key={`${step.step}-${tool.name}-${toolIndex}`}
                      className="tool-card"
                    >
                      <p className="tool-card__name">{tool.name}</p>
                      <p className="tool-card__label">Query</p>
                      <p className="tool-card__meta">{tool.query}</p>
                      <p className="tool-card__label">Result preview</p>
                      <p className="tool-card__preview">{tool.preview}</p>
                    </div>
                  ))}
                </div>
              )}

              <details className="execution-details">
                <summary>
                  {step.output ? 'View step output' : 'Waiting for output'}
                </summary>

                {step.output && (
                  <div className="execution-card__output markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {step.output}
                    </ReactMarkdown>
                  </div>
                )}
              </details>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
