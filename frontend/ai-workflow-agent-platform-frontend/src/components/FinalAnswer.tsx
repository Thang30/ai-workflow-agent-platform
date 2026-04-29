import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type {
  ConfidenceLevel,
  PlanStep,
  WorkflowAttempt,
  WorkflowRun,
  WorkflowTrace,
} from '../types/workflow';

type FinalAnswerProps = {
  workflowRun: WorkflowRun | null;
  selectedAttempt?: WorkflowAttempt | null;
  attempts?: WorkflowAttempt[];
  selectedPlan?: PlanStep[];
  selectedTraces?: WorkflowTrace[];
  status: string;
};

const getScoreTone = (score: number | null | undefined) => {
  if (score === null || score === undefined) {
    return '';
  }

  if (score >= 8) {
    return ' answer-evaluation--strong';
  }

  if (score >= 6) {
    return ' answer-evaluation--steady';
  }

  return ' answer-evaluation--weak';
};

const deriveConfidenceLevel = (
  score: number | null | undefined,
): ConfidenceLevel | null => {
  if (score === null || score === undefined) {
    return null;
  }

  if (score >= 8) {
    return 'high';
  }

  if (score >= 6) {
    return 'medium';
  }

  return 'low';
};

const getConfidenceLabel = (level: ConfidenceLevel | null) => {
  if (!level) {
    return null;
  }

  return `${level.slice(0, 1).toUpperCase()}${level.slice(1)}`;
};

export default function FinalAnswer({
  workflowRun,
  selectedAttempt,
  attempts = [],
  selectedPlan = [],
  selectedTraces = [],
  status,
}: FinalAnswerProps) {
  const result = selectedAttempt ?? workflowRun;
  const answer = result?.final_answer ?? '';
  const isFailed = result?.status === 'failed';
  const showEvaluation =
    result?.evaluation_score !== null && result?.evaluation_score !== undefined;
  const confidenceLevel =
    result?.confidence_level ?? deriveConfidenceLevel(result?.evaluation_score);
  const confidenceLabel = getConfidenceLabel(confidenceLevel);
  const reasoningSummary = result?.reasoning_summary ?? null;
  const toolGroups = selectedTraces.filter((trace) => trace.tools.length > 0);
  const hasExplainability =
    Boolean(reasoningSummary) ||
    selectedPlan.length > 0 ||
    toolGroups.length > 0;
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
                <div>
                  <p className="answer-evaluation__eyebrow">Evaluator</p>
                  <div className="answer-evaluation__score">
                    <span className="answer-evaluation__value">
                      {result.evaluation_score}
                    </span>
                    <span className="answer-evaluation__max">/10</span>
                  </div>
                </div>

                {confidenceLabel ? (
                  <div
                    className={`answer-confidence answer-confidence--${confidenceLevel}`}
                  >
                    <span className="answer-confidence__label">Confidence</span>
                    <span className="answer-confidence__value">
                      {confidenceLabel}
                    </span>
                  </div>
                ) : null}
              </div>

              {result.evaluation_reason ? (
                <p className="answer-evaluation__reason">
                  {result.evaluation_reason}
                </p>
              ) : null}
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

      {hasExplainability ? (
        <details className="answer-explainability">
          <summary>Show how this was generated</summary>

          <div className="answer-explainability__content">
            {reasoningSummary ? (
              <section className="answer-explainability__section">
                <p className="answer-explainability__eyebrow">
                  Reasoning summary
                </p>
                <p className="answer-explainability__summary">
                  {reasoningSummary}
                </p>
              </section>
            ) : null}

            {selectedPlan.length > 0 ? (
              <section className="answer-explainability__section">
                <p className="answer-explainability__eyebrow">Plan</p>
                <ol className="answer-explainability__plan-list">
                  {selectedPlan.map((step) => (
                    <li
                      key={`${step.step}-${step.description}`}
                      className="answer-explainability__plan-item"
                    >
                      <span className="answer-explainability__plan-step">
                        Step {step.step}
                      </span>
                      <span className="answer-explainability__plan-copy">
                        {step.description}
                      </span>
                    </li>
                  ))}
                </ol>
              </section>
            ) : null}

            {toolGroups.length > 0 ? (
              <section className="answer-explainability__section">
                <p className="answer-explainability__eyebrow">Tools used</p>
                <div className="answer-explainability__tool-groups">
                  {toolGroups.map((trace) => (
                    <div
                      key={`${trace.step}-${trace.description}`}
                      className="answer-explainability__tool-group"
                    >
                      <p className="answer-explainability__tool-heading">
                        Step {trace.step} · {trace.description}
                      </p>

                      <div className="answer-explainability__tool-list">
                        {trace.tools.map((tool, index) => (
                          <article
                            key={`${trace.step}-${tool.name}-${index}`}
                            className="answer-explainability__tool-item"
                          >
                            <p className="answer-explainability__tool-name">
                              {tool.name}
                            </p>
                            <p className="answer-explainability__tool-copy">
                              {tool.reason ??
                                'No tool-selection reason was recorded for this call.'}
                            </p>
                          </article>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            ) : null}
          </div>
        </details>
      ) : null}
    </section>
  );
}
