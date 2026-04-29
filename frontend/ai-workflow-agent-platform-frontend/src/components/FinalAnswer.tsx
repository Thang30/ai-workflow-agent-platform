import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { WorkflowRun } from '../types/workflow';

type FinalAnswerProps = {
  workflowRun: WorkflowRun | null;
  status: string;
};

export default function FinalAnswer({ workflowRun, status }: FinalAnswerProps) {
  const answer = workflowRun?.final_answer ?? '';

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
        <>
          {workflowRun ? (
            <div className="answer-evaluation">
              <div className="answer-evaluation__score-block">
                <p className="answer-evaluation__eyebrow">Evaluator</p>
                <div className="answer-evaluation__score">
                  <span className="answer-evaluation__value">
                    {workflowRun.evaluation_score}
                  </span>
                  <span className="answer-evaluation__max">/10</span>
                </div>
              </div>

              <p className="answer-evaluation__reason">
                {workflowRun.evaluation_reason}
              </p>
            </div>
          ) : null}

          <div className="answer-body">
            <p className="answer-body__eyebrow">Structured response</p>
            <div className="markdown-body answer-markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {answer}
              </ReactMarkdown>
            </div>
          </div>
        </>
      ) : (
        <div className="answer-empty">
          <div className="answer-empty__panel">
            <p className="answer-empty__eyebrow">Ready when the workflow is</p>
            <h4 className="answer-empty__title">
              The polished response lands here.
            </h4>
            <p className="answer-empty__copy">
              The planner outlines the work, the executor runs the steps, and
              the reviewer synthesizes the final answer before the evaluator
              scores it.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
