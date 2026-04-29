import { startTransition, useEffect, useState } from 'react';

import { getRun, getRunStats, listRuns } from '../api/client';
import FinalAnswer from '../components/FinalAnswer';
import PlanView from '../components/PlanView';
import TraceView from '../components/TraceView';
import type {
  WorkflowRunEnvelope,
  WorkflowRunStats,
  WorkflowRunSummary,
  WorkflowStatus,
  WorkflowStep,
  WorkflowTrace,
} from '../types/workflow';

const HISTORY_PAGE_SIZE = 20;

const formatDateTime = (value: string | null | undefined) => {
  if (!value) {
    return 'No timestamp yet';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatDuration = (durationMs: number | null | undefined) => {
  if (durationMs === null || durationMs === undefined) {
    return 'In progress';
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  const seconds = durationMs / 1000;
  return seconds >= 10 ? `${seconds.toFixed(0)} s` : `${seconds.toFixed(1)} s`;
};

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

const buildHistorySteps = (traces: WorkflowTrace[]): WorkflowStep[] => {
  return traces.map((trace) => ({
    step: trace.step,
    description: trace.description,
    status: 'done',
    output: trace.output,
    tools: trace.tools,
  }));
};

export default function RunHistoryPage() {
  const [runs, setRuns] = useState<WorkflowRunSummary[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedRun, setSelectedRun] = useState<WorkflowRunEnvelope | null>(
    null,
  );
  const [stats, setStats] = useState<WorkflowRunStats | null>(null);
  const [isListLoading, setIsListLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [listError, setListError] = useState('');
  const [detailError, setDetailError] = useState('');

  const loadRunDetail = async (runId: string) => {
    setIsDetailLoading(true);
    setDetailError('');

    try {
      const data = await getRun(runId);
      setSelectedRun(data);
    } catch {
      setSelectedRun(null);
      setDetailError('Unable to load the selected workflow run.');
    } finally {
      setIsDetailLoading(false);
    }
  };

  const refreshHistory = async () => {
    setIsListLoading(true);
    setListError('');

    try {
      const [statsData, runList] = await Promise.all([
        getRunStats(),
        listRuns(1, HISTORY_PAGE_SIZE),
      ]);

      setStats(statsData);
      setRuns(runList.items);

      const nextSelectedRunId = runList.items.some(
        (run) => run.id === selectedRunId,
      )
        ? selectedRunId
        : (runList.items[0]?.id ?? null);

      if (nextSelectedRunId && nextSelectedRunId === selectedRunId) {
        await loadRunDetail(nextSelectedRunId);
      } else {
        startTransition(() => {
          setSelectedRunId(nextSelectedRunId);
        });
      }

      if (!nextSelectedRunId) {
        setSelectedRun(null);
      }
    } catch {
      setRuns([]);
      setStats(null);
      setSelectedRun(null);
      setListError('Unable to load workflow history right now.');
      startTransition(() => {
        setSelectedRunId(null);
      });
    } finally {
      setIsListLoading(false);
    }
  };

  useEffect(() => {
    void refreshHistory();
  }, []);

  useEffect(() => {
    if (!selectedRunId) {
      setSelectedRun(null);
      setDetailError('');
      return;
    }

    void loadRunDetail(selectedRunId);
  }, [selectedRunId]);

  const selectedSummary = runs.find((run) => run.id === selectedRunId) ?? null;
  const detailRun = selectedRun?.workflow_run;
  const historySteps = selectedRun ? buildHistorySteps(selectedRun.traces) : [];

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
                onClick={() => {
                  void refreshHistory();
                }}
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
                    startTransition(() => {
                      setSelectedRunId(run.id);
                    });
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
                    {formatDuration(run.duration_ms)}
                  </p>

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
                ? `Status ${formatStatus(detailRun.status).toLowerCase()} · ${formatDuration(detailRun.duration_ms)}`
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
                    {formatDuration(detailRun.duration_ms)}
                  </p>
                </article>

                <article className="run-meta-card">
                  <p className="run-meta-card__label">Run ID</p>
                  <p className="run-meta-card__value run-meta-card__value--mono">
                    {detailRun.id}
                  </p>
                </article>
              </section>

              <div className="history-detail-stack">
                <PlanView
                  plan={selectedRun.plan}
                  steps={historySteps}
                  emptyMessage="This run failed before a plan was saved."
                />
                <TraceView
                  steps={historySteps}
                  emptyMessage="No execution traces were recorded for this run."
                />
                <FinalAnswer
                  workflowRun={detailRun}
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
