import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { WorkflowAttempt, WorkflowRun } from '../types/workflow';

type FinalAnswerProps = {
  workflowRun: WorkflowRun | null;
  selectedAttempt?: WorkflowAttempt | null;
  attempts?: WorkflowAttempt[];
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

export default function FinalAnswer({
  workflowRun,
  selectedAttempt,
  attempts = [],
  status,
}: FinalAnswerProps) {
  const result = selectedAttempt ?? workflowRun;
  const answer = result?.final_answer ?? '';
  const isFailed = result?.status === 'failed';
  const showEvaluation =
    result?.evaluation_score !== null &&
    result?.evaluation_score !== undefined &&
    result?.evaluation_reason;
  const selectedAttemptNumber =
    selectedAttempt?.attempt_number ??
    workflowRun?.selected_attempt_number ??
    null;
  const totalAttempts = attempts.length || workflowRun?.attempt_count || 0;
  const attemptSummary = attempts
    .map((attempt) => {
      const scoreLabel =
        attempt.evaluation_score === null ||
        attempt.evaluation_score === undefined
          ? attempt.status === 'failed'
            ? 'failed'
            : 'unscored'
          : `${attempt.evaluation_score}/10`;
      const selectedLabel =
        workflowRun?.selected_attempt_number === attempt.attempt_number
          ? ' selected'
          : '';
      return `Attempt ${attempt.attempt_number}: ${scoreLabel}${selectedLabel}`;
    })
    .join(' · ');

  const pillClassName = isFailed
    ? ' answer-pill--failed'
    : result?.status === 'running'
      ? ' answer-pill--running'
      : answer
        ? ' answer-pill--ready'
        : '';

  const pillLabel = isFailed
    ? 'Failed'
    : answer
      ? 'Reviewed'
      : result?.status === 'running'
        ? 'Running'
        : status || 'Waiting';

  return (
    <section className="answer-card">
      <div className="answer-card__header">
        <div>
          <p className="section-card__eyebrow">Reviewer</p>
          <h3 className="section-card__title">Final answer</h3>
          {selectedAttemptNumber ? (
            <p className="panel-banner__copy">
              Attempt {selectedAttemptNumber}
              {totalAttempts > 0 ? ` of ${totalAttempts}` : ''}
              {workflowRun?.selected_attempt_number === selectedAttemptNumber
                ? ' · Selected best attempt'
                : ''}
            </p>
          ) : null}
        </div>

        <span className={`answer-pill${pillClassName}`}>{pillLabel}</span>
      </div>

      {attemptSummary ? (
        <div className="answer-alert">
          <p className="answer-alert__label">Attempt scores</p>
          <p className="answer-alert__copy">{attemptSummary}</p>
        </div>
      ) : null}

      {selectedAttempt?.retry_trigger ? (
        <div className="answer-alert">
          <p className="answer-alert__label">Retry trigger</p>
          <p className="answer-alert__copy">{selectedAttempt.retry_trigger}</p>
        </div>
      ) : null}

      {result?.error_message ? (
        <div className="answer-alert">
          <p className="answer-alert__label">Workflow note</p>
          <p className="answer-alert__copy">{result.error_message}</p>
        </div>
      ) : null}

      {answer ? (
        <>
          {result && showEvaluation ? (
            <div
              className={`answer-evaluation${getScoreTone(result.evaluation_score)}`}
            >
              <div className="answer-evaluation__score-block">
                <p className="answer-evaluation__eyebrow">Evaluator</p>
                <div className="answer-evaluation__score">
                  <span className="answer-evaluation__value">
                    {result.evaluation_score}
                  </span>
                  <span className="answer-evaluation__max">/10</span>
                </div>
              </div>

              <p className="answer-evaluation__reason">
                {result.evaluation_reason}
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
