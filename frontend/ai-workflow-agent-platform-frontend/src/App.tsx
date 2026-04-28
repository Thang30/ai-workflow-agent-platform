import { useEffect, useRef, useState } from 'react';
import './App.css';
import { streamWorkflow } from './api/client';
import ChatInput from './components/ChatInput';
import PlanView from './components/PlanView';
import TraceView from './components/TraceView';
import FinalAnswer from './components/FinalAnswer';

type PlanStep = {
  step: number;
  description: string;
};

type WorkflowStep = PlanStep & {
  status: 'running' | 'done';
  output: string;
};

type WorkflowMessage =
  | { event: 'status'; data: string }
  | { event: 'plan'; data: PlanStep[] }
  | { event: 'step_start'; data: PlanStep }
  | { event: 'step_done'; data: { step: number; output: string } }
  | { event: 'final'; data: string };

function App() {
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [final, setFinal] = useState('');
  const [status, setStatus] = useState('');
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleStream = (query: string) => {
    eventSourceRef.current?.close();
    let completed = false;

    setStatus('Connecting...');
    setPlan([]);
    setSteps([]);
    setFinal('');

    const eventSource = streamWorkflow(query, {
      onMessage: (msg: WorkflowMessage) => {
        switch (msg.event) {
          case 'status':
            setStatus(msg.data);
            break;

          case 'plan':
            setPlan(msg.data);
            break;

          case 'step_start':
            setSteps((prev) => [
              ...prev,
              { ...msg.data, status: 'running', output: '' },
            ]);
            break;

          case 'step_done':
            setSteps((prev) =>
              prev.map((s) =>
                s.step === msg.data.step
                  ? { ...s, status: 'done', output: msg.data.output }
                  : s,
              ),
            );
            break;

          case 'final':
            completed = true;
            setFinal(msg.data);
            setStatus('Completed');
            eventSourceRef.current?.close();
            eventSourceRef.current = null;
            break;
        }
      },
    });

    eventSource.onerror = () => {
      if (completed) {
        return;
      }

      setStatus('Stream disconnected');
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
    };

    eventSourceRef.current = eventSource;
  };

  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
    };
  }, []);

  return (
    <div className="container">
      <h1 style={{ marginBottom: '20px' }}>🤖 AI Workflow Agent</h1>

      <ChatInput onSubmit={handleStream} />

      {status && (
        <div className="card">
          <p>{status}</p>
        </div>
      )}

      {plan.length > 0 && <PlanView plan={plan} />}
      {steps.length > 0 && <TraceView steps={steps} />}
      {final && <FinalAnswer answer={final} />}
    </div>
  );
}

export default App;
