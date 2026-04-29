export type ToolCall = {
  name: string;
  query: string;
  preview: string;
  raw_output?: unknown;
  started_at?: string;
  finished_at?: string;
  duration_ms?: number;
};

export type PlanStep = {
  step: number;
  description: string;
};

export type WorkflowStep = PlanStep & {
  status: 'running' | 'done';
  output: string;
  tools: ToolCall[];
};

export type WorkflowRun = {
  query: string;
  final_answer: string;
  evaluation_score: number;
  evaluation_reason: string;
};

export type WorkflowMessage =
  | { event: 'status'; data: string }
  | { event: 'plan'; data: PlanStep[] }
  | { event: 'step_start'; data: PlanStep }
  | {
      event: 'step_done';
      data: { step: number; output: string; tools?: ToolCall[] };
    }
  | { event: 'final'; data: WorkflowRun };

export type WorkflowEventName = WorkflowMessage['event'];
