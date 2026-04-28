import { useState } from 'react';
import { runWorkflow } from './api/client';
import ChatInput from './components/ChatInput';
import PlanView from './components/PlanView';
import TraceView from './components/TraceView';
import FinalAnswer from './components/FinalAnswer';

function App() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (query: string) => {
    setLoading(true);
    const result = await runWorkflow(query);
    setData(result);
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px' }}>
      <h1>AI Workflow Agent</h1>

      <ChatInput onSubmit={handleSubmit} />

      {loading && <p>Running workflow...</p>}

      {data && (
        <>
          <PlanView plan={data.plan} />
          <TraceView traces={data.traces} />
          <FinalAnswer answer={data.final} />
        </>
      )}
    </div>
  );
}

export default App;
