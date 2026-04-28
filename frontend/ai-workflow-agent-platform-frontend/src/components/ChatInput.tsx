import { useState, type FormEvent, type KeyboardEvent } from 'react';

type ChatInputProps = {
  onSubmit: (query: string) => void;
  isRunning: boolean;
};

export default function ChatInput({ onSubmit, isRunning }: ChatInputProps) {
  const [query, setQuery] = useState('');

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
            Cmd/Ctrl + Enter to run. Process stays on the left, result stays on
            the right.
          </p>

          <button
            className="composer__button"
            type="submit"
            disabled={!query.trim() || isRunning}
          >
            {isRunning ? 'Running...' : 'Run workflow'}
          </button>
        </div>
      </div>
    </form>
  );
}
