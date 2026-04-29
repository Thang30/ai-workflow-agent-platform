import axios from 'axios';

import type {
  AnalyticsDistribution,
  AnalyticsExperimentSummary,
  AnalyticsSummary,
  AnalyticsTimeSeries,
  AnalyticsToolUsageList,
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
    'experiment_assigned',
    'attempt_start',
    'attempt_complete',
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

export const runWorkflow = async (query: string) => {
  const response = await apiClient.post<WorkflowRunEnvelope>('/workflow', {
    query,
  });

  return response.data;
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

export const getAnalyticsSummary = async (days = 7) => {
  const response = await apiClient.get<AnalyticsSummary>('/analytics/summary', {
    params: { days },
  });

  return response.data;
};

export const getAnalyticsTimeseries = async (days = 7) => {
  const response = await apiClient.get<AnalyticsTimeSeries>(
    '/analytics/timeseries',
    {
      params: { days },
    },
  );

  return response.data;
};

export const getAnalyticsDistribution = async (days = 7) => {
  const response = await apiClient.get<AnalyticsDistribution>(
    '/analytics/distribution',
    {
      params: { days },
    },
  );

  return response.data;
};

export const getAnalyticsTools = async (days = 7) => {
  const response = await apiClient.get<AnalyticsToolUsageList>(
    '/analytics/tools',
    {
      params: { days },
    },
  );

  return response.data;
};

export const getAnalyticsExperimentSummary = async (days = 7) => {
  const response = await apiClient.get<AnalyticsExperimentSummary | null>(
    '/analytics/experiment-summary',
    {
      params: { days },
    },
  );

  return response.data;
};
