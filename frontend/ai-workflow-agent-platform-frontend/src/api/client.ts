import axios from 'axios';

import type {
  WorkflowEventName,
  WorkflowMessage,
  WorkflowRunEnvelope,
  WorkflowRunList,
  WorkflowRunStats,
} from '../types/workflow';

type StreamHandlers = {
  onMessage: (message: WorkflowMessage) => void;
};

const API_URL = import.meta.env.VITE_API_URL;

const apiClient = axios.create({
  baseURL: API_URL,
});

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

export const listRuns = async (page = 1, pageSize = 20) => {
  const response = await apiClient.get<WorkflowRunList>('/runs', {
    params: { page, page_size: pageSize },
  });

  return response.data;
};

export const getRun = async (runId: string) => {
  const response = await apiClient.get<WorkflowRunEnvelope>(`/runs/${runId}`);
  return response.data;
};

export const getRunStats = async () => {
  const response = await apiClient.get<WorkflowRunStats>('/runs/stats');
  return response.data;
};
