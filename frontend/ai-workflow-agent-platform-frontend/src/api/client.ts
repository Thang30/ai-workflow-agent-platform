type WorkflowEventName =
  | 'status'
  | 'plan'
  | 'step_start'
  | 'step_done'
  | 'final';

type PlanStep = {
  step: number;
  description: string;
};

type WorkflowMessage =
  | { event: 'status'; data: string }
  | { event: 'plan'; data: PlanStep[] }
  | { event: 'step_start'; data: PlanStep }
  | { event: 'step_done'; data: { step: number; output: string } }
  | { event: 'final'; data: string };

type StreamHandlers = {
  onMessage: (message: WorkflowMessage) => void;
};

export const streamWorkflow = (query: string, handlers: StreamHandlers) => {
  const eventSource = new EventSource(
    `http://localhost:8000/workflow/stream?query=${encodeURIComponent(query)}`,
  );

  const events: WorkflowEventName[] = [
    'status',
    'plan',
    'step_start',
    'step_done',
    'final',
  ];

  for (const eventName of events) {
    eventSource.addEventListener(eventName, (event) => {
      const messageEvent = event as MessageEvent<string>;
      handlers.onMessage({
        event: eventName,
        data: JSON.parse(messageEvent.data),
      } as WorkflowMessage);
    });
  }

  return eventSource;
};
