type DurationFormatOptions = {
  emptyText?: string | null;
  roundMilliseconds?: boolean;
  includeSeconds?: boolean;
};

export const formatDurationMs = (
  durationMs: number | null | undefined,
  options: DurationFormatOptions = {},
): string | null => {
  const {
    emptyText = null,
    roundMilliseconds = false,
    includeSeconds = true,
  } = options;

  if (durationMs === null || durationMs === undefined) {
    return emptyText;
  }

  if (!includeSeconds || durationMs < 1000) {
    const milliseconds = roundMilliseconds
      ? Math.round(durationMs)
      : durationMs;
    return `${milliseconds} ms`;
  }

  const seconds = durationMs / 1000;
  return seconds >= 10 ? `${seconds.toFixed(0)} s` : `${seconds.toFixed(1)} s`;
};

export const formatToolDurationMs = (durationMs?: number): string | null => {
  if (durationMs === undefined) {
    return null;
  }

  return `${durationMs >= 100 ? Math.round(durationMs) : durationMs.toFixed(2)} ms`;
};

export const formatDateTime = (
  value: string | null | undefined,
  emptyText = 'No timestamp yet',
): string => {
  if (!value) {
    return emptyText;
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

export const formatTimeOfDay = (value?: string): string | null => {
  if (!value) {
    return null;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};
