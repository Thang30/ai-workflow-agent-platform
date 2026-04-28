import { useState } from 'react';

export default function ChatInput({ onSubmit }: any) {
  const [query, setQuery] = useState('');

  return (
    <div className="card">
      <input
        style={{
          width: '70%',
          padding: '10px',
          borderRadius: '8px',
          border: 'none',
          marginRight: '10px',
        }}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your query..."
      />
      <button
        style={{
          padding: '10px 16px',
          borderRadius: '8px',
          background: '#3b82f6',
          color: 'white',
          border: 'none',
          cursor: 'pointer',
        }}
        onClick={() => onSubmit(query)}
      >
        Run
      </button>
    </div>
  );
}
