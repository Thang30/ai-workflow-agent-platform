import { startTransition, useCallback, useEffect, useState } from 'react';

import { getRun, getRunStats, listRuns } from '../api/client';
import FinalAnswer from '../components/FinalAnswer';
import PlanView from '../components/PlanView';
import TraceView from '../components/TraceView';
import { formatDateTime, formatDurationMs } from '../utils/formatters';
import {
  buildWorkflowSteps,
  getSelectedAttempt,
} from '../utils/workflowRunView';
import type {
  WorkflowAttempt,
  WorkflowRunEnvelope,
  WorkflowRun,
  WorkflowRunStats,
  WorkflowRunSummary,
  WorkflowStatus,
} from '../types/workflow';

const HISTORY_PAGE_SIZE = 20;

const formatStatus = (status: WorkflowStatus) => {
  switch (status) {
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    default:
      return 'Running';
  }
};

const formatExperimentLabel = (
  experiment:
    | WorkflowRunSummary['experiment']
    | WorkflowRun['experiment']
    | WorkflowAttempt['experiment']
    | null
    | undefined,
) => {
  if (!experiment) {
    return 'No experiment';
  }

  return `${experiment.experiment_name} · Variant ${experiment.variant_name}`;
};

export default function RunHistoryPage() {
  const [runs, setRuns] = useState<WorkflowRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedAttemptNumber, setSelectedAttemptNumber] = useState<
    number | null
  >(null);
  const [selectedRun, setSelectedRun] = useState<WorkflowRunEnvelope | null>(
    null,
  );
  const [stats, setStats] = useState<WorkflowRunStats | null>(null);
  const [isListLoading, setIsListLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [listError, setListError] = useState('');
  const [detailError, setDetailError] = useState('');

  const loadRunDetail = useCallback(async (runId: string) => {
    try {
      const data = await getRun(runId);
      setSelectedRun(data);
      setSelectedAttemptNumber(
        data.workflow_run?.selected_attempt_number ??
          data.attempts.at(-1)?.attempt_number ??
          null,
      );
      setDetailError('');
    } catch {
      setSelectedRun(null);
      setSelectedAttemptNumber(null);
      setDetailError('Unable to load the selected workflow run.');
    } finally {
      setIsDetailLoading(false);
    }
  }, []);

  const refreshHistory = useCallback(
    async (currentSelectedRunId: string | null) => {
      try {
        const [statsData, runList] = await Promise.all([
          getRunStats(),
          listRuns(1, HISTORY_PAGE_SIZE),
        ]);

        setStats(statsData);
        setRuns(runList.items);

        const nextSelectedRunId = runList.items.some(
          (run) => run.id === currentSelectedRunId,
        )
          ? currentSelectedRunId
          : (runList.items[0]?.id ?? null);

        if (!nextSelectedRunId) {
          setSelectedRun(null);
          setSelectedAttemptNumber(null);
          setDetailError('');
          setIsDetailLoading(false);

          if (currentSelectedRunId !== null) {
            startTransition(() => {
              setSelectedRunId(null);
            });
          }

          return;
        }

        setIsDetailLoading(true);
        setDetailError('');

        startTransition(() => {
          setSelectedRunId(nextSelectedRunId);
        });

        await loadRunDetail(nextSelectedRunId);
      } catch {
        setRuns([]);
        setStats(null);
        setSelectedRun(null);
        setSelectedAttemptNumber(null);
        setDetailError('');
        setIsDetailLoading(false);
        setListError('Unable to load workflow history right now.');
        startTransition(() => {
          setSelectedRunId(null);
        });
      } finally {
        setIsListLoading(false);
      }
    },
    [loadRunDetail],
  );

  const handleRefresh = () => {
    setIsListLoading(true);
    setListError('');
    void refreshHistory(selectedRunId);
  };

  const handleSelectRun = (runId: string) => {
    if (runId === selectedRunId) {
      return;
    }

    setIsDetailLoading(true);
    setDetailError('');

    startTransition(() => {
      setSelectedRunId(runId);
    });

    void loadRunDetail(runId);
  };

  useEffect(() => {
    let isCancelled = false;

    queueMicrotask(() => {
      if (!isCancelled) {
        void refreshHistory(null);
      }
    });

    return () => {
      isCancelled = true;
    };
  }, [refreshHistory]);

  const selectedSummary = runs.find((run) => run.id === selectedRunId) ?? null;
  const detailRun = selectedRun?.workflow_run ?? null;
  const attempts = selectedRun?.attempts ?? [];
  const selectedAttempt: WorkflowAttempt | null = getSelectedAttempt(
    detailRun,
    attempts,
    selectedAttemptNumber,
  );
  const selectedPlan = selectedAttempt?.plan ?? selectedRun?.plan ?? [];
  const selectedTraces = selectedAttempt?.traces ?? selectedRun?.traces ?? [];
  const historySteps = buildWorkflowSteps(selectedTraces);

  return (
    <>
      <header className="hero hero--history">
        <div className="hero__badge">Persistent run archive</div>
        <div className="hero__content">
          <p className="hero__eyebrow">
            History - diagnostics - replay context
          </p>
          <h2>Workflow run history</h2>
          <p className="hero__lede">
            Browse completed and failed runs, inspect their saved plans and
            traces, and review the final answers and evaluator signals after the
            live stream has ended.
          </p>
        </div>
      </header>

      <section className="history-overview">
        <article className="overview-card">
          <p className="overview-card__label">Total runs</p>
          <p className="overview-card__value">{stats?.total_runs ?? 0}</p>
        </article>
        <article className="overview-card">
          <p className="overview-card__label">Average score</p>
          <p className="overview-card__value">
            {stats?.average_score ?? 'No scored runs'}
          </p>
        </article>
        <article className="overview-card">
          <p className="overview-card__label">Last run</p>
          <p className="overview-card__value overview-card__value--small">
            {formatDateTime(stats?.last_run_at)}
          </p>
        </article>
      </section>

      <main className="history-grid">
        <section className="workspace-panel history-panel">
          <div className="panel-banner">
            <div>
              <p className="panel-banner__eyebrow">Archive</p>
              <h2>Recent runs</h2>
            </div>

            <div className="history-actions">
              <p className="panel-banner__copy">Newest runs appear first.</p>
              <button
                type="button"
                className="history-refresh"
                onClick={handleRefresh}
              >
                Refresh
              </button>
            </div>
          </div>

          {listError ? (
            <div className="empty-state">{listError}</div>
          ) : isListLoading ? (
            <div className="empty-state">Loading workflow history...</div>
          ) : runs.length === 0 ? (
            <div className="empty-state">
              No persisted workflow runs yet. Execute a workflow from the live
              page to populate this history view.
            </div>
          ) : (
            <div className="history-list">
              {runs.map((run) => (
                <button
                  key={run.id}
                  type="button"
                  className={`history-list__item${run.id === selectedRunId ? ' history-list__item--selected' : ''}`}
                  onClick={() => {
                    handleSelectRun(run.id);
                  }}
                >
                  <div className="history-list__top">
                    <p className="history-list__title">{run.query}</p>
                    <span className={`status-chip status-chip--${run.status}`}>
                      {formatStatus(run.status)}
                    </span>
                  </div>

                  <p className="history-list__meta">
                    {formatDateTime(run.created_at)} ·{' '}
                    {formatDurationMs(run.duration_ms, {
                      emptyText: 'In progress',
                    })}{' '}
                    · {run.attempt_count}{' '}
                    {run.attempt_count === 1 ? 'attempt' : 'attempts'}
                  </p>

                  {run.experiment ? (
                    <p className="history-list__meta history-list__meta--accent">
                      {formatExperimentLabel(run.experiment)}
                    </p>
                  ) : null}

                  <p className="history-list__preview">
                    {run.final_answer ??
                      run.error_message ??
                      'Plan and trace data saved for inspection.'}
                  </p>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="workspace-panel history-panel history-panel--detail">
          <div className="panel-banner">
            <div>
              <p className="panel-banner__eyebrow">Selected run</p>
              <h2>{selectedSummary?.query ?? 'Workflow details'}</h2>
            </div>

            <p className="panel-banner__copy">
              {detailRun
                ? `Status ${formatStatus(detailRun.status).toLowerCase()} · ${formatDurationMs(detailRun.duration_ms, { emptyText: 'In progress' })}`
                : 'Choose a run to inspect its saved plan, traces, and answer.'}
            </p>
          </div>

          {detailError ? (
            <div className="empty-state">{detailError}</div>
          ) : isDetailLoading ? (
            <div className="empty-state">Loading run details...</div>
          ) : !selectedRun || !detailRun ? (
            <div className="empty-state">
              Select a run from the left-hand list to inspect its details.
            </div>
          ) : (
            <>
              <section className="history-run-meta">
                <article className="run-meta-card">
                  <p className="run-meta-card__label">Status</p>
                  <p className="run-meta-card__value">
                    {formatStatus(detailRun.status)}
                  </p>
                </article>

                <article className="run-meta-card">
                  <p className="run-meta-card__label">Started</p>
                  <p className="run-meta-card__value">
                    {formatDateTime(detailRun.created_at)}
                  </p>
                </article>

                <article className="run-meta-card">
                  <p className="run-meta-card__label">Duration</p>
                  <p className="run-meta-card__value">
                    {formatDurationMs(detailRun.duration_ms, {
                      emptyText: 'In progress',
                    })}
                  </p>
                </article>

                <article className="run-meta-card">
                  <p className="run-meta-card__label">Attempts</p>
                  <p className="run-meta-card__value">
                    {detailRun.attempt_count}
                  </p>
                </article>

                <article className="run-meta-card">
                  <p className="run-meta-card__label">Experiment</p>
                  <p className="run-meta-card__value run-meta-card__value--small">
                    {formatExperimentLabel(
                      selectedAttempt?.experiment ?? detailRun.experiment,
                    )}
                  </p>
                </article>

                <article className="run-meta-card">
                  <p className="run-meta-card__label">Run ID</p>
                  <p className="run-meta-card__value run-meta-card__value--mono">
                    {detailRun.id}
                  </p>
                </article>
              </section>

              {attempts.length > 0 ? (
                <section className="history-overview">
                  {attempts.map((attempt) => (
                    <button
                      key={attempt.id}
                      type="button"
                      className={`history-refresh${attempt.attempt_number === selectedAttemptNumber ? ' analytics-filter analytics-filter--active' : ' analytics-filter'}`}
                      onClick={() => {
                        setSelectedAttemptNumber(attempt.attempt_number);
                      }}
                    >
                      Attempt {attempt.attempt_number}
                      {attempt.evaluation_score !== null &&
                      attempt.evaluation_score !== undefined
                        ? ` · ${attempt.evaluation_score}/10`
                        : attempt.status === 'failed'
                          ? ' · failed'
                          : ''}
                      {detailRun.selected_attempt_number ===
                      attempt.attempt_number
                        ? ' · selected'
                        : ''}
                      {attempt.experiment
                        ? ` · ${attempt.experiment.variant_name}`
                        : ''}
                    </button>
                  ))}
                </section>
              ) : null}

              <div className="history-detail-stack">
                <PlanView
                  plan={selectedPlan}
                  steps={historySteps}
                  emptyMessage="This run failed before a plan was saved."
                />
                <TraceView
                  steps={historySteps}
                  emptyMessage="No execution traces were recorded for this run."
                />
                <FinalAnswer
                  workflowRun={detailRun}
                  selectedAttempt={selectedAttempt}
                  attempts={attempts}
                  selectedPlan={selectedPlan}
                  selectedTraces={selectedTraces}
                  status={formatStatus(detailRun.status)}
                />
              </div>
            </>
          )}
        </section>
      </main>
    </>
  );
}
