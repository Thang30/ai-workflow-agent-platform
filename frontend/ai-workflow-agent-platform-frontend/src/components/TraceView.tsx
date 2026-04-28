import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type WorkflowStep = {
  step: number;
  description: string;
  status: 'running' | 'done';
  output: string;
};

type TraceViewProps = {
  steps: WorkflowStep[];
};

export default function TraceView({ steps }: TraceViewProps) {
  return (
    <div className="card">
      <h2>⚙️ Execution</h2>

      {steps.map((s) => (
        <div
          key={s.step}
          className={`execution-step execution-step--${s.status}`}
        >
          <strong className="execution-step__title">
            Step {s.step}: {s.description}
          </strong>

          <p className="execution-step__status">
            {s.status === 'running' ? '⏳ Running...' : '✅ Done'}
          </p>

          {s.output && (
            <div className="execution-step__output markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{s.output}</ReactMarkdown>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
