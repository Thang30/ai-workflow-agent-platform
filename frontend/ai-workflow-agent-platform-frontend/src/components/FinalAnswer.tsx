import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type FinalAnswerProps = {
  answer: string;
  status: string;
};

export default function FinalAnswer({ answer, status }: FinalAnswerProps) {
  return (
    <section className="answer-card">
      <div className="answer-card__header">
        <div>
          <p className="section-card__eyebrow">Reviewer</p>
          <h3 className="section-card__title">Final answer</h3>
        </div>

        <span className={`answer-pill${answer ? ' answer-pill--ready' : ''}`}>
          {answer ? 'Reviewed' : status || 'Waiting'}
        </span>
      </div>

      {answer ? (
        <div className="answer-body">
          <p className="answer-body__eyebrow">Structured response</p>
          <div className="markdown-body answer-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
          </div>
        </div>
      ) : (
        <div className="answer-empty">
          <div className="answer-empty__panel">
            <p className="answer-empty__eyebrow">Ready when the workflow is</p>
            <h4 className="answer-empty__title">
              The polished response lands here.
            </h4>
            <p className="answer-empty__copy">
              The planner outlines the work, the executor runs the steps, and
              the reviewer synthesizes the final answer once the trace is
              complete.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
