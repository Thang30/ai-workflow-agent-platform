import type {
  WorkflowAttempt,
  WorkflowRun,
  WorkflowStep,
  WorkflowTrace,
} from '../types/workflow';

export const buildWorkflowSteps = (traces: WorkflowTrace[]): WorkflowStep[] => {
  return traces.map((trace) => ({
    step: trace.step,
    description: trace.description,
    status: 'done',
    output: trace.output,
    tools: trace.tools,
  }));
};

export const getSelectedAttempt = (
  workflowRun: WorkflowRun | null,
  attempts: WorkflowAttempt[],
  attemptNumber?: number | null,
): WorkflowAttempt | null => {
  if (!workflowRun) {
    return null;
  }

  if (attemptNumber !== null && attemptNumber !== undefined) {
    return (
      attempts.find((attempt) => attempt.attempt_number === attemptNumber) ??
      null
    );
  }

  return (
    attempts.find(
      (attempt) =>
        attempt.attempt_number === workflowRun.selected_attempt_number,
    ) ??
    attempts.at(-1) ??
    null
  );
};
