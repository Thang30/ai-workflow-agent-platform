import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { WorkflowStep } from '../types/workflow';

type TraceViewProps = {
  steps: WorkflowStep[];
  emptyMessage?: string;
};

const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) {
    return null;
  }

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

const formatDuration = (durationMs?: number) => {
  if (durationMs === undefined) {
    return null;
  }

  return `${durationMs >= 100 ? Math.round(durationMs) : durationMs.toFixed(2)} ms`;
};

const formatRawOutput = (rawOutput: unknown) => {
  if (rawOutput === undefined) {
    return '';
  }

  if (typeof rawOutput === 'string') {
    return rawOutput;
  }

  return JSON.stringify(rawOutput, null, 2);
};

export default function TraceView({ steps, emptyMessage }: TraceViewProps) {
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
          {emptyMessage ??
            'As each planned step starts, it appears here with status, tool usage, and expandable output.'}
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
                      <p className="tool-card__label">Tool input</p>
                      <pre className="tool-card__raw tool-card__input">
                        {tool.input || tool.query}
                      </pre>

                      {tool.reason ? (
                        <>
                          <p className="tool-card__label">Why it was used</p>
                          <p className="tool-card__reason">{tool.reason}</p>
                        </>
                      ) : null}

                      {(tool.started_at ||
                        tool.finished_at ||
                        tool.duration_ms !== undefined) && (
                        <div className="tool-card__metrics">
                          {tool.started_at && (
                            <span className="tool-card__metric">
                              Started {formatTimestamp(tool.started_at)}
                            </span>
                          )}

                          {tool.finished_at && (
                            <span className="tool-card__metric">
                              Finished {formatTimestamp(tool.finished_at)}
                            </span>
                          )}

                          {tool.duration_ms !== undefined && (
                            <span className="tool-card__metric">
                              Duration {formatDuration(tool.duration_ms)}
                            </span>
                          )}
                        </div>
                      )}

                      <p className="tool-card__label">Result preview</p>
                      <p className="tool-card__preview">{tool.preview}</p>

                      {tool.raw_output !== undefined && (
                        <details className="tool-card__details">
                          <summary>View raw tool output</summary>
                          <pre className="tool-card__raw">
                            {formatRawOutput(tool.raw_output)}
                          </pre>
                        </details>
                      )}
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
