import { startTransition, useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {
  getAnalyticsDistribution,
  getAnalyticsSummary,
  getAnalyticsTimeseries,
  getAnalyticsTools,
} from '../api/client';
import type {
  AnalyticsDistribution,
  AnalyticsSummary,
  AnalyticsTimeSeries,
  AnalyticsToolUsageList,
} from '../types/workflow';

const ANALYTICS_WINDOWS = [1, 7, 30] as const;

const DISTRIBUTION_COLORS: Record<string, string> = {
  '0_5': '#f87171',
  '6_7': '#fbbf24',
  '8_10': '#34d399',
};

type AnalyticsWindow = (typeof ANALYTICS_WINDOWS)[number];

const chartDateFormatter = new Intl.DateTimeFormat([], {
  month: 'short',
  day: 'numeric',
});

const formatScore = (value: number | null) => {
  if (value === null) {
    return 'No scored runs';
  }

  return `${value.toFixed(2)} / 10`;
};

const formatRate = (value: number | null) => {
  if (value === null) {
    return 'No completed runs';
  }

  return `${Math.round(value * 100)}%`;
};

const formatDuration = (value: number | null) => {
  if (value === null) {
    return 'No completed runs';
  }

  if (value < 1000) {
    return `${Math.round(value)} ms`;
  }

  const seconds = value / 1000;
  return seconds >= 10 ? `${seconds.toFixed(0)} s` : `${seconds.toFixed(1)} s`;
};

const formatCompactDuration = (value: number | null | undefined) => {
  if (value === null || value === undefined) {
    return '—';
  }

  if (value < 1000) {
    return `${Math.round(value)} ms`;
  }

  const seconds = value / 1000;
  return seconds >= 10 ? `${seconds.toFixed(0)} s` : `${seconds.toFixed(1)} s`;
};

const formatChartDay = (value: string) => {
  const date = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return chartDateFormatter.format(date);
};

const formatTooltipValue = (value: number | string | null | undefined, label: string) => {
  if (typeof value !== 'number') {
    return [value ?? '—', label];
  }

  if (label === 'Avg score') {
    return [`${value.toFixed(2)} / 10`, label];
  }

  if (label.includes('duration')) {
    return [formatCompactDuration(value), label];
  }

  if (label === 'Failure rate') {
    return [`${value.toFixed(1)}%`, label];
  }

  if (label === 'Tool share') {
    return [`${value.toFixed(1)}%`, label];
  }

  return [value, label];
};

const buildInsights = (
  summary: AnalyticsSummary | null,
  timeseries: AnalyticsTimeSeries | null,
  tools: AnalyticsToolUsageList | null,
) => {
  const insights: string[] = [];

  if (summary?.average_score !== null && summary?.average_score !== undefined) {
    if (summary.average_score >= 8) {
      insights.push('Average score is in the strong band for the selected window.');
    } else if (summary.average_score < 6) {
      insights.push('Average score is below the current pass threshold and needs attention.');
    }
  }

  if (summary?.failure_rate !== null && summary?.failure_rate !== undefined) {
    if (summary.failure_rate >= 0.25) {
      insights.push('Failure rate is elevated for this window, so reliability is the first thing to inspect.');
    } else if (summary.failure_rate <= 0.1) {
      insights.push('Failure rate is low in this window, which suggests the workflow is operating steadily.');
    }
  }

  const activePoints = timeseries?.items.filter((item) => item.total_runs > 0) ?? [];
  if (activePoints.length >= 2) {
    const firstPoint = activePoints[0];
    const lastPoint = activePoints[activePoints.length - 1];
    if (
      firstPoint.average_score !== null &&
      lastPoint.average_score !== null
    ) {
      const delta = lastPoint.average_score - firstPoint.average_score;
      if (Math.abs(delta) >= 0.25) {
        insights.push(
          delta > 0
            ? `Average score improved by ${delta.toFixed(2)} points across the active days in view.`
            : `Average score declined by ${Math.abs(delta).toFixed(2)} points across the active days in view.`,
        );
      }
    }
  }

  const topTool = tools?.items[0];
  if (topTool) {
    insights.push(
      `${topTool.name} is the dominant tool at ${Math.round(topTool.share * 100)}% of recorded tool calls.`,
    );
  }

  if (summary?.p95_duration_ms) {
    insights.push(
      `P95 completion time is ${formatDuration(summary.p95_duration_ms)}, which highlights the slower end of the run distribution.`,
    );
  }

  return insights.slice(0, 4);
};

export default function AnalyticsPage() {
  const [days, setDays] = useState<AnalyticsWindow>(7);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [timeseries, setTimeseries] = useState<AnalyticsTimeSeries | null>(null);
  const [distribution, setDistribution] = useState<AnalyticsDistribution | null>(null);
  const [tools, setTools] = useState<AnalyticsToolUsageList | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadAnalytics = async () => {
      setIsLoading(true);
      setError('');

      try {
        const [summaryData, timeseriesData, distributionData, toolsData] =
          await Promise.all([
            getAnalyticsSummary(days),
            getAnalyticsTimeseries(days),
            getAnalyticsDistribution(days),
            getAnalyticsTools(days),
          ]);

        setSummary(summaryData);
        setTimeseries(timeseriesData);
        setDistribution(distributionData);
        setTools(toolsData);
      } catch {
        setSummary(null);
        setTimeseries(null);
        setDistribution(null);
        setTools(null);
        setError('Unable to load analytics right now.');
      } finally {
        setIsLoading(false);
      }
    };

    void loadAnalytics();
  }, [days]);

  const insights = buildInsights(summary, timeseries, tools);
  const timeseriesChartData = (timeseries?.items ?? []).map((item) => ({
    ...item,
    label: formatChartDay(item.date),
    failure_rate_percent:
      item.failure_rate === null ? null : Number((item.failure_rate * 100).toFixed(1)),
  }));
  const hasTimeseriesData = timeseriesChartData.some((item) => item.total_runs > 0);
  const distributionChartData = distribution?.items ?? [];
  const hasDistributionData = distributionChartData.some((item) => item.count > 0);
  const toolChartData = (tools?.items ?? []).slice(0, 5).map((tool) => ({
    ...tool,
    label:
      tool.name.length > 18 ? `${tool.name.slice(0, 18).trimEnd()}…` : tool.name,
    share_percent: Number((tool.share * 100).toFixed(1)),
  }));
  const hasToolData = toolChartData.length > 0;

  return (
    <>
      <header className="hero hero--analytics">
        <div className="hero__badge">Analytics cockpit</div>
        <div className="hero__content">
          <p className="hero__eyebrow">Quality - reliability - performance</p>
          <h2>Workflow analytics</h2>
          <p className="hero__lede">
            Track how the workflow is performing across score quality, failure
            rate, latency, and tool usage so prompt and orchestration changes
            can be measured instead of guessed.
          </p>
        </div>
      </header>

      <section className="analytics-toolbar">
        <div className="analytics-toolbar__copy">
          <p className="panel-banner__eyebrow">Time window</p>
          <p className="panel-banner__copy">
            Completed and failed runs only. In-progress runs are excluded from
            analytics.
          </p>
        </div>

        <div className="analytics-toolbar__actions" role="group" aria-label="Analytics window">
          {ANALYTICS_WINDOWS.map((windowValue) => (
            <button
              key={windowValue}
              type="button"
              className={`history-refresh${windowValue === days ? ' analytics-filter analytics-filter--active' : ' analytics-filter'}`}
              onClick={() => {
                startTransition(() => {
                  setDays(windowValue);
                });
              }}
            >
              Last {windowValue}d
            </button>
          ))}
        </div>
      </section>

      {error ? <div className="empty-state">{error}</div> : null}

      <section className="history-overview analytics-overview">
        <article className="overview-card">
          <p className="overview-card__label">Average score</p>
          <p className="overview-card__value">{formatScore(summary?.average_score ?? null)}</p>
        </article>
        <article className="overview-card">
          <p className="overview-card__label">Failure rate</p>
          <p className="overview-card__value">{formatRate(summary?.failure_rate ?? null)}</p>
        </article>
        <article className="overview-card">
          <p className="overview-card__label">Average time</p>
          <p className="overview-card__value">{formatDuration(summary?.average_duration_ms ?? null)}</p>
        </article>
        <article className="overview-card">
          <p className="overview-card__label">Total runs</p>
          <p className="overview-card__value">{summary?.total_runs ?? 0}</p>
        </article>
      </section>

      <main className="analytics-grid">
        <section className="workspace-panel analytics-panel analytics-panel--charts">
          <div className="panel-banner">
            <div>
              <p className="panel-banner__eyebrow">Signals</p>
              <h2>Dashboard charts</h2>
            </div>

            <p className="panel-banner__copy">
              {isLoading
                ? 'Loading analytics signals...'
                : 'Trends and distributions come directly from persisted workflow runs.'}
            </p>
          </div>

          <div className="analytics-card-grid">
            <article className="section-card analytics-card">
              <div className="section-card__header">
                <div>
                  <p className="section-card__eyebrow">Score over time</p>
                  <h3 className="section-card__title">Trend</h3>
                </div>
                <p className="section-card__meta">{timeseries?.items.length ?? 0} points</p>
              </div>
              {isLoading ? (
                <div className="analytics-placeholder">Loading trend data...</div>
              ) : hasTimeseriesData ? (
                <div className="analytics-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={timeseriesChartData}>
                      <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis
                        yAxisId="score"
                        domain={[0, 10]}
                        tickCount={6}
                        tickLine={false}
                        axisLine={false}
                        width={36}
                      />
                      <YAxis
                        yAxisId="volume"
                        orientation="right"
                        allowDecimals={false}
                        tickLine={false}
                        axisLine={false}
                        width={30}
                      />
                      <Tooltip
                        formatter={(value, name) =>
                          formatTooltipValue(
                            typeof value === 'number' ? value : null,
                            name === 'average_score' ? 'Avg score' : 'Runs',
                          )
                        }
                        labelFormatter={(value) => `Day: ${value}`}
                        contentStyle={{
                          borderRadius: '18px',
                          border: '1px solid rgba(148, 163, 184, 0.18)',
                          background: 'rgba(8, 15, 27, 0.96)',
                        }}
                      />
                      <Legend />
                      <Bar
                        yAxisId="volume"
                        dataKey="total_runs"
                        name="Runs"
                        fill="rgba(148, 163, 184, 0.28)"
                        radius={[10, 10, 4, 4]}
                      />
                      <Line
                        yAxisId="score"
                        type="monotone"
                        dataKey="average_score"
                        name="Avg score"
                        stroke="#60a5fa"
                        strokeWidth={3}
                        dot={false}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="analytics-placeholder">No completed runs in the selected window.</div>
              )}
            </article>

            <article className="section-card analytics-card">
              <div className="section-card__header">
                <div>
                  <p className="section-card__eyebrow">Score distribution</p>
                  <h3 className="section-card__title">Quality spread</h3>
                </div>
                <p className="section-card__meta">Three score bands</p>
              </div>
              {isLoading ? (
                <div className="analytics-placeholder">Loading score distribution...</div>
              ) : hasDistributionData ? (
                <div className="analytics-chart analytics-chart--compact">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distributionChartData}>
                      <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} tickLine={false} axisLine={false} width={30} />
                      <Tooltip
                        formatter={(value) => formatTooltipValue(typeof value === 'number' ? value : null, 'Runs')}
                        contentStyle={{
                          borderRadius: '18px',
                          border: '1px solid rgba(148, 163, 184, 0.18)',
                          background: 'rgba(8, 15, 27, 0.96)',
                        }}
                      />
                      <Bar dataKey="count" radius={[10, 10, 4, 4]}>
                        {distributionChartData.map((bucket) => (
                          <Cell
                            key={bucket.key}
                            fill={DISTRIBUTION_COLORS[bucket.key] ?? '#60a5fa'}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="analytics-placeholder">No score distribution yet.</div>
              )}
            </article>

            <article className="section-card analytics-card">
              <div className="section-card__header">
                <div>
                  <p className="section-card__eyebrow">Tool usage</p>
                  <h3 className="section-card__title">Behavior</h3>
                </div>
                <p className="section-card__meta">Calls and run share</p>
              </div>
              {isLoading ? (
                <div className="analytics-placeholder">Loading tool usage...</div>
              ) : hasToolData ? (
                <div className="analytics-chart analytics-chart--compact">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={toolChartData} layout="vertical" margin={{ left: 12 }}>
                      <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" horizontal={false} />
                      <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
                      <YAxis
                        type="category"
                        dataKey="label"
                        tickLine={false}
                        axisLine={false}
                        width={110}
                      />
                      <Tooltip
                        formatter={(value, name) =>
                          formatTooltipValue(
                            typeof value === 'number' ? value : null,
                            name === 'share_percent' ? 'Tool share' : 'Calls',
                          )
                        }
                        labelFormatter={(value, payload) => {
                          const item = payload?.[0]?.payload as { name?: string } | undefined;
                          return item?.name ?? String(value);
                        }}
                        contentStyle={{
                          borderRadius: '18px',
                          border: '1px solid rgba(148, 163, 184, 0.18)',
                          background: 'rgba(8, 15, 27, 0.96)',
                        }}
                      />
                      <Bar
                        dataKey="call_count"
                        name="Calls"
                        fill="#34d399"
                        radius={[0, 10, 10, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="analytics-placeholder">No tool calls recorded in this window.</div>
              )}
              {hasToolData ? (
                <div className="analytics-list analytics-list--metrics">
                  {toolChartData.map((tool) => (
                    <div key={tool.name} className="analytics-list__item analytics-list__item--stacked">
                      <span>{tool.name}</span>
                      <strong>{tool.share_percent}%</strong>
                    </div>
                  ))}
                </div>
              ) : null}
            </article>

            <article className="section-card analytics-card">
              <div className="section-card__header">
                <div>
                  <p className="section-card__eyebrow">Latency</p>
                  <h3 className="section-card__title">Tail performance</h3>
                </div>
                <p className="section-card__meta">P95 {formatCompactDuration(summary?.p95_duration_ms)}</p>
              </div>
              {isLoading ? (
                <div className="analytics-placeholder">Loading latency trend...</div>
              ) : hasTimeseriesData ? (
                <div className="analytics-chart analytics-chart--compact">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={timeseriesChartData}>
                      <defs>
                        <linearGradient id="analyticsLatencyFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.35} />
                          <stop offset="100%" stopColor="#38bdf8" stopOpacity={0.03} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid stroke="rgba(148, 163, 184, 0.12)" vertical={false} />
                      <XAxis dataKey="label" tickLine={false} axisLine={false} />
                      <YAxis tickLine={false} axisLine={false} width={44} />
                      <Tooltip
                        formatter={(value) =>
                          formatTooltipValue(
                            typeof value === 'number' ? value : null,
                            'Avg duration',
                          )
                        }
                        labelFormatter={(value) => `Day: ${value}`}
                        contentStyle={{
                          borderRadius: '18px',
                          border: '1px solid rgba(148, 163, 184, 0.18)',
                          background: 'rgba(8, 15, 27, 0.96)',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="average_duration_ms"
                        name="Avg duration"
                        stroke="#38bdf8"
                        fill="url(#analyticsLatencyFill)"
                        strokeWidth={3}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="analytics-placeholder">No latency data in the selected window.</div>
              )}
            </article>
          </div>
        </section>

        <aside className="workspace-panel analytics-panel analytics-panel--insights">
          <div className="panel-banner">
            <div>
              <p className="panel-banner__eyebrow">Insights</p>
              <h2>What changed</h2>
            </div>
          </div>

          {isLoading ? (
            <div className="empty-state">Loading analytics insights...</div>
          ) : insights.length > 0 ? (
            <div className="analytics-insights">
              {insights.map((insight) => (
                <article key={insight} className="analytics-insight-card">
                  <p className="analytics-insight-card__eyebrow">Signal</p>
                  <p className="analytics-insight-card__copy">{insight}</p>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              Run a few completed workflows to populate analytics insights.
            </div>
          )}
        </aside>
      </main>
    </>
  );
}