import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { WorkflowRun } from '../types/workflow';

type FinalAnswerProps = {
  workflowRun: WorkflowRun | null;
  status: string;
};

const getScoreTone = (score: number | null | undefined) => {
  if (score === null || score === undefined) {
    return '';
  }

  if (score >= 8) {
    return ' answer-evaluation--strong';
  }

  if (score >= 5) {
    return ' answer-evaluation--steady';
  }

  return ' answer-evaluation--weak';
};

export default function FinalAnswer({ workflowRun, status }: FinalAnswerProps) {
  const answer = workflowRun?.final_answer ?? '';
  const isFailed = workflowRun?.status === 'failed';
  const showEvaluation =
    workflowRun?.evaluation_score !== null &&
    workflowRun?.evaluation_score !== undefined &&
    workflowRun?.evaluation_reason;

  const pillClassName = isFailed
    ? ' answer-pill--failed'
    : workflowRun?.status === 'running'
      ? ' answer-pill--running'
      : answer
        ? ' answer-pill--ready'
        : '';

  const pillLabel = isFailed
    ? 'Failed'
    : answer
      ? 'Reviewed'
      : workflowRun?.status === 'running'
        ? 'Running'
        : status || 'Waiting';

  return (
    <section className="answer-card">
      <div className="answer-card__header">
        <div>
          <p className="section-card__eyebrow">Reviewer</p>
          <h3 className="section-card__title">Final answer</h3>
        </div>

        <span className={`answer-pill${pillClassName}`}>{pillLabel}</span>
      </div>

      {workflowRun?.error_message ? (
        <div className="answer-alert">
          <p className="answer-alert__label">Workflow note</p>
          <p className="answer-alert__copy">{workflowRun.error_message}</p>
        </div>
      ) : null}

      {answer ? (
        <>
          {workflowRun && showEvaluation ? (
            <div
              className={`answer-evaluation${getScoreTone(workflowRun.evaluation_score)}`}
            >
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
      ) : isFailed ? (
        <div className="answer-empty answer-empty--failure">
          <div className="answer-empty__panel">
            <p className="answer-empty__eyebrow">Workflow failed</p>
            <h4 className="answer-empty__title">
              This run stopped before it produced a final answer.
            </h4>
            <p className="answer-empty__copy">
              The saved plan and traces still appear alongside this panel so you
              can inspect how far the workflow progressed.
            </p>
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
              the reviewer synthesizes the final answer before the evaluator
              scores it.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
