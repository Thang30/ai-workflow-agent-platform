import { useState } from 'react';

export default function ChatInput({ onSubmit }: any) {
  const [query, setQuery] = useState('');

  return (
    <div>
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter your query..."
      />
      <button onClick={() => onSubmit(query)}>Run</button>
    </div>
  );
}
