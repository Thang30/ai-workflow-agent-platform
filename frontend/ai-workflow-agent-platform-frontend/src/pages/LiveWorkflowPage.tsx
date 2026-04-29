import { useEffect, useRef, useState } from 'react';

import { streamWorkflow } from '../api/client';
import ChatInput from '../components/ChatInput';
import FinalAnswer from '../components/FinalAnswer';
import PlanView from '../components/PlanView';
import TraceView from '../components/TraceView';
import type {
  ExperimentAssignment,
  PlanStep,
  WorkflowAttempt,
  WorkflowMessage,
  WorkflowRun,
  WorkflowRunEnvelope,
  WorkflowStep,
  WorkflowTrace,
} from '../types/workflow';

const buildWorkflowSteps = (traces: WorkflowTrace[]): WorkflowStep[] => {
  return traces.map((trace) => ({
    step: trace.step,
    description: trace.description,
    status: 'done',
    output: trace.output,
    tools: trace.tools,
  }));
};

const formatDuration = (durationMs: number | null | undefined) => {
  if (durationMs === null || durationMs === undefined) {
    return '—';
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  const seconds = durationMs / 1000;
  return seconds >= 10 ? `${seconds.toFixed(0)} s` : `${seconds.toFixed(1)} s`;
};

const getSelectedAttempt = (payload: WorkflowRunEnvelope | null) => {
  if (!payload?.workflow_run) {
    return null;
  }

  return (
    payload.attempts.find(
      (attempt) =>
        attempt.attempt_number ===
        payload.workflow_run?.selected_attempt_number,
    ) ??
    payload.attempts.at(-1) ??
    null
  );
};

type DemoSuiteCase = {
  id: string;
  label: string;
  query: string;
  passingScore: number;
};

const DEMO_SUITE: DemoSuiteCase[] = [
  {
    id: 'finland-job-market',
    label: 'Finland job market',
    query:
      'Research only Finland for remote backend Python roles in 2026. Use at most 3 web lookups and stop once you can report 4 concise bullets: current demand signal, common skills, one salary signal if clearly available, and one caveat about the data. If salary data is not clearly available, say that instead of broadening the search. Do not compare with other countries or expand beyond Finland.',
    passingScore: 7,
  },
  {
    id: 'calculate-loan-interest',
    label: 'Calculate loan interest',
    query:
      'Calculate the monthly payment and total interest for a $350,000 mortgage at 6.5% APR over 30 years. Show the formula, the result, and a short plain-English explanation.',
    passingScore: 9,
  },
  {
    id: 'compare-ai-models',
    label: 'Compare AI models',
    query:
      'Compare GPT-4.1, Claude 3.7 Sonnet, and Gemini 2.5 Pro for an enterprise coding assistant. Summarize strengths, tradeoffs, and end with a clear recommendation.',
    passingScore: 8,
  },
];

type DemoSuiteStatus = 'idle' | 'queued' | 'running' | 'completed' | 'failed';

type DemoSuiteResult = DemoSuiteCase & {
  status: DemoSuiteStatus;
  envelope: WorkflowRunEnvelope | null;
  errorMessage: string | null;
};

type DemoSuiteOutcomeTone = 'pass' | 'fail' | 'workflow-failed';

type WorkflowStreamOptions = {
  clearSuiteSelection?: boolean;
  onFinal?: (payload: WorkflowRunEnvelope) => void;
  onError?: () => void;
  onStatus?: (nextStatus: string) => void;
};

const getSuiteTone = (status: DemoSuiteStatus) => {
  switch (status) {
    case 'completed':
      return 'done';
    case 'failed':
      return 'failed';
    case 'running':
      return 'active';
    case 'queued':
      return 'queued';
    default:
      return 'idle';
  }
};

const getSuiteLabel = (status: DemoSuiteStatus) => {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    case 'running':
      return 'Running';
    case 'queued':
      return 'Queued';
    default:
      return 'Ready';
  }
};

const getSuiteOutcome = (entry: DemoSuiteResult) => {
  if (entry.envelope?.workflow_run?.status === 'failed') {
    return {
      label: 'Workflow failed',
      tone: 'workflow-failed' as DemoSuiteOutcomeTone,
    };
  }

  const score = entry.envelope?.workflow_run?.evaluation_score;
  if (score === null || score === undefined) {
    return null;
  }

  if (score >= entry.passingScore) {
    return { label: 'Pass', tone: 'pass' as DemoSuiteOutcomeTone };
  }

  return { label: 'Fail', tone: 'fail' as DemoSuiteOutcomeTone };
};

export default function LiveWorkflowPage() {
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [workflowRun, setWorkflowRun] = useState<WorkflowRun | null>(null);
  const [attempts, setAttempts] = useState<WorkflowAttempt[]>([]);
  const [currentAttemptNumber, setCurrentAttemptNumber] = useState<
    number | null
  >(null);
  const [assignedExperiment, setAssignedExperiment] =
    useState<ExperimentAssignment | null>(null);
  const [status, setStatus] = useState('');
  const [isSuiteRunning, setIsSuiteRunning] = useState(false);
  const [suiteStatus, setSuiteStatus] = useState('');
  const [suiteResults, setSuiteResults] = useState<DemoSuiteResult[]>([]);
  const [selectedSuiteResultId, setSelectedSuiteResultId] = useState<
    string | null
  >(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const resetRunView = (nextStatus = 'Connecting...') => {
    setStatus(nextStatus);
    setPlan([]);
    setSteps([]);
    setWorkflowRun(null);
    setAttempts([]);
    setCurrentAttemptNumber(null);
    setAssignedExperiment(null);
  };

  const hydrateRunView = (payload: WorkflowRunEnvelope) => {
    const nextWorkflowRun = payload.workflow_run;
    const nextSelectedAttempt = getSelectedAttempt(payload);

    setWorkflowRun(nextWorkflowRun);
    setAttempts(payload.attempts);
    setAssignedExperiment(nextWorkflowRun?.experiment ?? null);
    setCurrentAttemptNumber(
      nextWorkflowRun?.selected_attempt_number ??
        nextSelectedAttempt?.attempt_number ??
        null,
    );
    setPlan(nextSelectedAttempt?.plan ?? payload.plan);
    setSteps(buildWorkflowSteps(nextSelectedAttempt?.traces ?? payload.traces));
    setStatus(nextWorkflowRun?.status === 'failed' ? 'Failed' : 'Completed');
  };

  const handleSelectSuiteResult = (entry: DemoSuiteResult) => {
    if (!entry.envelope) {
      return;
    }

    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setSelectedSuiteResultId(entry.id);
    hydrateRunView(entry.envelope);
  };

  const handleWorkflowMessage = (
    msg: WorkflowMessage,
    options?: Pick<WorkflowStreamOptions, 'onFinal' | 'onStatus'>,
  ) => {
    switch (msg.event) {
      case 'status':
        setStatus(msg.data);
        options?.onStatus?.(msg.data);
        break;

      case 'experiment_assigned':
        setAssignedExperiment(msg.data);
        break;

      case 'attempt_start':
        setCurrentAttemptNumber(msg.data.attempt_number);
        setPlan([]);
        setSteps([]);
        break;

      case 'attempt_complete':
        setAttempts((prev) => {
          const next = prev.filter(
            (attempt) => attempt.attempt_number !== msg.data.attempt_number,
          );
          return [...next, msg.data].sort(
            (left, right) => left.attempt_number - right.attempt_number,
          );
        });
        break;

      case 'plan':
        setCurrentAttemptNumber(msg.data.attempt_number);
        setPlan(msg.data.plan);
        break;

      case 'step_start':
        setCurrentAttemptNumber(msg.data.attempt_number);
        setSteps((prev) => {
          const existingStep = prev.find((step) => step.step === msg.data.step);

          if (existingStep) {
            return prev.map((step) =>
              step.step === msg.data.step
                ? {
                    ...step,
                    step: msg.data.step,
                    description: msg.data.description,
                    status: 'running',
                    output: '',
                    tools: [],
                  }
                : step,
            );
          }

          return [
            ...prev,
            {
              step: msg.data.step,
              description: msg.data.description,
              status: 'running',
              output: '',
              tools: [],
            },
          ];
        });
        break;

      case 'step_done':
        setCurrentAttemptNumber(msg.data.attempt_number);
        setSteps((prev) => {
          const existingStep = prev.find((step) => step.step === msg.data.step);

          if (!existingStep) {
            return [
              ...prev,
              {
                step: msg.data.step,
                description: `Step ${msg.data.step}`,
                status: 'done',
                output: msg.data.output,
                tools: msg.data.tools ?? [],
              },
            ];
          }

          return prev.map((step) =>
            step.step === msg.data.step
              ? {
                  ...step,
                  status: 'done',
                  output: msg.data.output,
                  tools: msg.data.tools ?? [],
                }
              : step,
          );
        });
        break;

      case 'final':
        hydrateRunView(msg.data);
        options?.onFinal?.(msg.data);
        eventSourceRef.current?.close();
        eventSourceRef.current = null;
        break;
    }
  };

  const startWorkflowStream = (
    query: string,
    options?: WorkflowStreamOptions,
  ) => {
    eventSourceRef.current?.close();
    let completed = false;

    resetRunView();
    if (options?.clearSuiteSelection) {
      setSelectedSuiteResultId(null);
    }

    const eventSource = streamWorkflow(query, {
      onMessage: (msg: WorkflowMessage) => {
        if (msg.event === 'final') {
          completed = true;
        }

        handleWorkflowMessage(msg, options);
      },
    });

    eventSource.onerror = () => {
      if (completed) {
        return;
      }

      setStatus('Stream disconnected');
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
      options?.onError?.();
    };

    eventSourceRef.current = eventSource;
  };

  const handleStream = (query: string) => {
    startWorkflowStream(query, {
      clearSuiteSelection: true,
    });
  };

  const handleRunSuite = async () => {
    const initialResults: DemoSuiteResult[] = DEMO_SUITE.map((item) => ({
      ...item,
      status: 'queued',
      envelope: null,
      errorMessage: null,
    }));

    setSuiteResults(initialResults);
    setSuiteStatus(`Running ${DEMO_SUITE.length} demo prompts...`);
    setIsSuiteRunning(true);
    setSelectedSuiteResultId(null);

    for (const item of DEMO_SUITE) {
      setSuiteStatus(`Running ${item.label}...`);
      setSelectedSuiteResultId(item.id);
      setSuiteResults((prev) =>
        prev.map((entry) =>
          entry.id === item.id ? { ...entry, status: 'running' } : entry,
        ),
      );

      await new Promise<void>((resolve) => {
        startWorkflowStream(item.query, {
          onStatus: (nextStatus) => {
            setSuiteStatus(`${item.label}: ${nextStatus}`);
          },
          onFinal: (envelope) => {
            const nextStatus =
              envelope.workflow_run?.status === 'failed'
                ? 'failed'
                : 'completed';

            setSuiteResults((prev) =>
              prev.map((entry) =>
                entry.id === item.id
                  ? {
                      ...entry,
                      status: nextStatus,
                      envelope,
                      errorMessage:
                        envelope.workflow_run?.error_message ?? null,
                    }
                  : entry,
              ),
            );
            resolve();
          },
          onError: () => {
            setSuiteStatus(`${item.label}: Stream disconnected`);
            setSuiteResults((prev) =>
              prev.map((entry) =>
                entry.id === item.id
                  ? {
                      ...entry,
                      status: 'failed',
                      errorMessage:
                        'The stream disconnected before this workflow completed.',
                    }
                  : entry,
              ),
            );
            resolve();
          },
        });
      });
    }

    setSuiteStatus('Demo suite completed. Runs were saved to history.');
    setIsSuiteRunning(false);
  };

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  const completedSteps = steps.filter((step) => step.status === 'done').length;
  const selectedAttempt =
    attempts.find(
      (attempt) => attempt.attempt_number === currentAttemptNumber,
    ) ??
    (workflowRun?.selected_attempt_number
      ? attempts.find(
          (attempt) =>
            attempt.attempt_number === workflowRun.selected_attempt_number,
        )
      : null) ??
    attempts.at(-1) ??
    null;
  const isLiveRunning =
    Boolean(status) &&
    status !== 'Completed' &&
    status !== 'Failed' &&
    status !== 'Stream disconnected';
  const isBusy = isLiveRunning || isSuiteRunning;
  const currentExperiment =
    selectedAttempt?.experiment ??
    workflowRun?.experiment ??
    assignedExperiment;
  const renderedSuiteResults: DemoSuiteResult[] = DEMO_SUITE.map(
    (item) =>
      suiteResults.find((entry) => entry.id === item.id) ?? {
        ...item,
        status: 'idle',
        envelope: null,
        errorMessage: null,
      },
  );
  const completedSuiteCount = renderedSuiteResults.filter(
    (entry) => entry.status === 'completed' || entry.status === 'failed',
  ).length;
  const suiteScores = renderedSuiteResults
    .map((entry) => entry.envelope?.workflow_run?.evaluation_score)
    .filter((score): score is number => score !== null && score !== undefined);
  const averageSuiteScore = suiteScores.length
    ? (
        suiteScores.reduce((sum, score) => sum + score, 0) / suiteScores.length
      ).toFixed(1)
    : null;
  const passedSuiteCount = renderedSuiteResults.filter((entry) => {
    const outcome = getSuiteOutcome(entry);
    return outcome?.tone === 'pass';
  }).length;

  const stages = [
    {
      icon: '🧠',
      label: 'Planner',
      detail:
        plan.length > 0
          ? `${plan.length} steps mapped`
          : 'Breaks the request into a strategy',
      tone: status.includes('Planning')
        ? 'active'
        : plan.length > 0
          ? 'done'
          : 'idle',
    },
    {
      icon: '⚙️',
      label: 'Executor',
      detail:
        steps.length > 0
          ? `${completedSteps}/${steps.length} steps finished`
          : 'Runs steps and calls tools',
      tone: status.includes('Executing')
        ? 'active'
        : steps.length > 0 &&
            (Boolean(workflowRun) ||
              status.includes('Reviewing') ||
              status.includes('Evaluating'))
          ? 'done'
          : steps.length > 0
            ? 'active'
            : 'idle',
    },
    {
      icon: '🔍',
      label: 'Reviewer',
      detail:
        workflowRun || status.includes('Evaluating')
          ? 'Final answer synthesized'
          : 'Shapes the response for delivery',
      tone: status.includes('Reviewing')
        ? 'active'
        : workflowRun || status.includes('Evaluating')
          ? 'done'
          : 'idle',
    },
    {
      icon: '📏',
      label: 'Evaluator',
      detail:
        workflowRun?.evaluation_score !== null &&
        workflowRun?.evaluation_score !== undefined
          ? `${workflowRun.evaluation_score}/10 with rationale`
          : workflowRun?.status === 'failed'
            ? 'Skipped after workflow failure'
            : 'Scores the answer and explains why',
      tone: status.includes('Evaluating')
        ? 'active'
        : workflowRun
          ? 'done'
          : 'idle',
    },
  ] as const;

  return (
    <>
      <header className="hero">
        <div className="hero__badge">Portfolio workflow demo</div>
        <div className="hero__content">
          <p className="hero__eyebrow">
            Planner - Executor - Reviewer - Evaluator
          </p>
          <h2>Live workflow trace</h2>
          <p className="hero__lede">
            A process-first interface that shows how the system plans work,
            executes steps, uses tools, and delivers a reviewed and scored
            answer in real time.
          </p>
        </div>
      </header>

      <ChatInput
        onSubmit={handleStream}
        isRunning={isLiveRunning}
        isSuiteRunning={isSuiteRunning}
        presets={[...DEMO_SUITE]}
        onRunSuite={() => {
          if (!isBusy) {
            void handleRunSuite();
          }
        }}
      />

      <section className="suite-panel">
        <div className="suite-panel__header">
          <div>
            <p className="section-card__eyebrow">Demo suite</p>
            <h3 className="section-card__title">Batch scorecard</h3>
          </div>

          <p className="suite-panel__status">
            {suiteStatus ||
              'Run the canned prompts in sequence and compare scores.'}
          </p>
        </div>

        <div className="suite-panel__overview">
          <article className="suite-kpi">
            <p className="suite-kpi__label">Cases</p>
            <p className="suite-kpi__value">{DEMO_SUITE.length}</p>
          </article>
          <article className="suite-kpi">
            <p className="suite-kpi__label">Completed</p>
            <p className="suite-kpi__value">
              {completedSuiteCount}/{DEMO_SUITE.length}
            </p>
          </article>
          <article className="suite-kpi">
            <p className="suite-kpi__label">Passed</p>
            <p className="suite-kpi__value">
              {passedSuiteCount}/{DEMO_SUITE.length}
            </p>
          </article>
          <article className="suite-kpi">
            <p className="suite-kpi__label">Avg score</p>
            <p className="suite-kpi__value">
              {averageSuiteScore ? `${averageSuiteScore}/10` : '—'}
            </p>
          </article>
        </div>

        <div className="suite-panel__list">
          {renderedSuiteResults.map((entry) => {
            const outcome = getSuiteOutcome(entry);
            const isSelected = selectedSuiteResultId === entry.id;

            return (
              <article
                key={entry.id}
                className={`suite-case suite-case--${getSuiteTone(entry.status)}${isSelected ? ' suite-case--selected' : ''}`}
              >
                <div className="suite-case__header">
                  <div>
                    <p className="suite-case__label">{entry.label}</p>
                    <p className="suite-case__query">{entry.query}</p>
                  </div>

                  <div className="suite-case__badges">
                    <span className="suite-case__badge">
                      {getSuiteLabel(entry.status)}
                    </span>
                    {outcome ? (
                      <span
                        className={`suite-case__verdict suite-case__verdict--${outcome.tone}`}
                      >
                        {outcome.label}
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="suite-case__meta">
                  <span>
                    Score:{' '}
                    {entry.envelope?.workflow_run?.evaluation_score !== null &&
                    entry.envelope?.workflow_run?.evaluation_score !== undefined
                      ? `${entry.envelope.workflow_run.evaluation_score}/10`
                      : '—'}
                  </span>
                  <span>Threshold: {entry.passingScore}/10</span>
                  <span>
                    Attempts:{' '}
                    {entry.envelope?.workflow_run?.attempt_count ?? '—'}
                  </span>
                  <span>
                    Duration:{' '}
                    {formatDuration(entry.envelope?.workflow_run?.duration_ms)}
                  </span>
                </div>

                <div className="suite-case__actions">
                  <button
                    type="button"
                    className="suite-case__load-button"
                    disabled={!entry.envelope}
                    onClick={() => handleSelectSuiteResult(entry)}
                  >
                    {isSelected
                      ? 'Showing in main panels'
                      : 'Show in main panels'}
                  </button>
                </div>

                {entry.errorMessage ? (
                  <p className="suite-case__error">{entry.errorMessage}</p>
                ) : null}
              </article>
            );
          })}
        </div>

        <p className="suite-panel__note">
          Each batch run is stored automatically, so the full details also show
          up in Run history and Analytics. Use Show in main panels to inspect a
          specific suite run in the trace and final-answer views.
        </p>
      </section>

      <main className="workspace-grid">
        <section className="workspace-panel">
          <div className="panel-banner">
            <div>
              <p className="panel-banner__eyebrow">Process</p>
              <h2>Live workflow trace</h2>
            </div>

            <p className="panel-banner__copy">
              Follow the plan, execution, and tool usage as the workflow moves
              from intent to answer.
            </p>
          </div>

          <div className="status-board">
            {stages.map((stage) => (
              <article
                key={stage.label}
                className={`stage-card stage-card--${stage.tone}`}
              >
                <p className="stage-card__label">
                  <span>{stage.icon}</span>
                  {stage.label}
                </p>
                <p className="stage-card__detail">{stage.detail}</p>
              </article>
            ))}
          </div>

          <div className="live-status">
            <span
              className={`live-status__dot${isLiveRunning ? ' live-status__dot--active' : ''}`}
            />
            <span>{status || 'Waiting for a workflow request.'}</span>
          </div>

          {currentExperiment ? (
            <div className="experiment-context">
              <span className="experiment-context__badge">Experiment</span>
              <p className="experiment-context__copy">
                {currentExperiment.experiment_name} · Variant{' '}
                {currentExperiment.variant_name}
              </p>
            </div>
          ) : null}

          <PlanView plan={plan} steps={steps} />
          <TraceView steps={steps} />
        </section>

        <section className="workspace-panel workspace-panel--answer">
          <div className="panel-banner panel-banner--answer">
            <div>
              <p className="panel-banner__eyebrow">Result</p>
              <h2>Presentation-ready answer</h2>
            </div>

            <p className="panel-banner__copy">
              The reviewer consolidates every step into a clean, polished final
              response, and the evaluator adds a light-touch quality check.
            </p>
          </div>

          <FinalAnswer
            workflowRun={workflowRun}
            selectedAttempt={selectedAttempt}
            attempts={attempts}
            selectedPlan={selectedAttempt?.plan ?? []}
            selectedTraces={selectedAttempt?.traces ?? []}
            status={status}
          />
        </section>
      </main>
    </>
  );
}
