import { useState, type FormEvent, type KeyboardEvent } from 'react';

type PromptPreset = {
  label: string;
  query: string;
};

type ChatInputProps = {
  onSubmit: (query: string) => void;
  isRunning: boolean;
  isSuiteRunning?: boolean;
  presets?: PromptPreset[];
  onRunSuite?: () => void;
};

export default function ChatInput({
  onSubmit,
  isRunning,
  isSuiteRunning = false,
  presets = [],
  onRunSuite,
}: ChatInputProps) {
  const [query, setQuery] = useState('');
  const isBusy = isRunning || isSuiteRunning;

  const submitQuery = () => {
    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      return;
    }

    onSubmit(trimmedQuery);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    submitQuery();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      submitQuery();
    }
  };

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <div className="composer__field">
        <div className="composer__header">
          <p className="composer__eyebrow">Workflow input</p>
          <p className="composer__summary">
            Ask the system to research, compare, evaluate, or summarize.
          </p>
        </div>

        {presets.length > 0 ? (
          <div className="composer__preset-row">
            <p className="composer__label composer__label--inline">
              Demo prompts
            </p>
            <div className="composer__preset-list">
              {presets.map((preset) => (
                <button
                  key={preset.label}
                  type="button"
                  className="composer__preset"
                  disabled={isBusy}
                  title={preset.query}
                  onClick={() => setQuery(preset.query)}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <label className="composer__label" htmlFor="workflow-query">
          Describe what you want the agent workflow to do.
        </label>

        <textarea
          id="workflow-query"
          className="composer__textarea"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Example: Compare Nvidia and AMD positioning in AI infrastructure, highlight revenue drivers, and end with a concise recommendation."
          rows={4}
        />

        <div className="composer__actions">
          <p className="composer__hint">
            Cmd/Ctrl + Enter runs a live workflow. Demo prompts can preload the
            editor, or you can run the full suite in batch.
          </p>

          <div className="composer__action-buttons">
            {onRunSuite ? (
              <button
                className="composer__ghost-button"
                type="button"
                disabled={isBusy}
                onClick={onRunSuite}
              >
                {isSuiteRunning
                  ? `Running suite...`
                  : `Run demo suite (${presets.length})`}
              </button>
            ) : null}

            <button
              className="composer__button"
              type="submit"
              disabled={!query.trim() || isBusy}
            >
              {isRunning
                ? 'Running live...'
                : isSuiteRunning
                  ? 'Suite running...'
                  : 'Run workflow'}
            </button>
          </div>
        </div>
      </div>
    </form>
  );
}
