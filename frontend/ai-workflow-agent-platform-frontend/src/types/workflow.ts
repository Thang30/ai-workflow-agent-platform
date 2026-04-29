export type ToolCall = {
  name: string;
  query: string;
  preview: string;
  raw_output?: unknown;
  success?: boolean;
  error_message?: string | null;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
};

export type PlanStep = {
  step: number;
  description: string;
};

export type WorkflowStatus = 'running' | 'completed' | 'failed';

export type WorkflowTrace = {
  step: number;
  description: string;
  input: string;
  output: string;
  tools: ToolCall[];
};

export type WorkflowStep = PlanStep & {
  status: 'running' | 'done';
  output: string;
  tools: ToolCall[];
};

export type WorkflowRun = {
  id: string;
  query: string;
  status: WorkflowStatus;
  created_at: string;
  attempt_count: number;
  selected_attempt_number: number | null;
  final_answer: string | null;
  evaluation_score: number | null;
  evaluation_reason: string | null;
  duration_ms: number | null;
  completed_at: string | null;
  error_message: string | null;
};

export type WorkflowAttempt = {
  id: string;
  run_id: string;
  attempt_number: number;
  status: WorkflowStatus;
  created_at: string;
  retry_trigger: string | null;
  improvement_hint: string | null;
  had_tool_failure: boolean;
  final_answer: string | null;
  evaluation_score: number | null;
  evaluation_reason: string | null;
  duration_ms: number | null;
  completed_at: string | null;
  error_message: string | null;
  plan: PlanStep[];
  traces: WorkflowTrace[];
};

export type WorkflowRunEnvelope = {
  input: string;
  plan: PlanStep[];
  traces: WorkflowTrace[];
  final: string | null;
  workflow_run: WorkflowRun | null;
  attempts: WorkflowAttempt[];
};

export type WorkflowRunSummary = {
  id: string;
  query: string;
  status: WorkflowStatus;
  created_at: string;
  attempt_count: number;
  selected_attempt_number: number | null;
  final_answer: string | null;
  evaluation_score: number | null;
  duration_ms: number | null;
  completed_at: string | null;
  error_message: string | null;
};

export type WorkflowRunList = {
  items: WorkflowRunSummary[];
  page: number;
  page_size: number;
  total: number;
};

export type WorkflowRunStats = {
  total_runs: number;
  average_score: number | null;
  last_run_at: string | null;
};

export type AnalyticsSummary = {
  total_runs: number;
  average_score: number | null;
  failure_rate: number | null;
  average_duration_ms: number | null;
  p95_duration_ms: number | null;
  retry_rate: number | null;
  successful_retry_rate: number | null;
  average_attempts_per_run: number | null;
  average_score_improvement: number | null;
};

export type AnalyticsTimeSeriesPoint = {
  date: string;
  total_runs: number;
  average_score: number | null;
  failure_rate: number | null;
  average_duration_ms: number | null;
  retry_rate: number | null;
  average_attempts_per_run: number | null;
  average_score_improvement: number | null;
};

export type AnalyticsTimeSeries = {
  items: AnalyticsTimeSeriesPoint[];
};

export type AnalyticsDistributionBucket = {
  key: string;
  label: string;
  count: number;
};

export type AnalyticsDistribution = {
  items: AnalyticsDistributionBucket[];
};

export type AnalyticsToolUsage = {
  name: string;
  call_count: number;
  run_count: number;
  share: number;
  average_duration_ms: number | null;
};

export type AnalyticsToolUsageList = {
  items: AnalyticsToolUsage[];
};

export type WorkflowMessage =
  | { event: 'status'; data: string }
  | {
      event: 'attempt_start';
      data: {
        attempt_number: number;
        retry_trigger: string | null;
        improvement_hint: string | null;
      };
    }
  | { event: 'attempt_complete'; data: WorkflowAttempt }
  | { event: 'plan'; data: { attempt_number: number; plan: PlanStep[] } }
  | {
      event: 'step_start';
      data: { attempt_number: number; step: number; description: string };
    }
  | {
      event: 'step_done';
      data: {
        attempt_number: number;
        step: number;
        output: string;
        tools?: ToolCall[];
      };
    }
  | { event: 'final'; data: WorkflowRunEnvelope };

export type WorkflowEventName = WorkflowMessage['event'];
