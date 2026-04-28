import type { WorkflowEventName, WorkflowMessage } from '../types/workflow';

type StreamHandlers = {
  onMessage: (message: WorkflowMessage) => void;
};

const API_URL = import.meta.env.VITE_API_URL;

export const streamWorkflow = (query: string, handlers: StreamHandlers) => {
  const eventSource = new EventSource(
    `${API_URL}/workflow/stream?query=${encodeURIComponent(query)}`,
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
