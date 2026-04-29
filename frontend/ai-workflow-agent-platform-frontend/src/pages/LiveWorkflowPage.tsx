import { useEffect, useRef, useState } from 'react';

import { streamWorkflow } from '../api/client';
import ChatInput from '../components/ChatInput';
import FinalAnswer from '../components/FinalAnswer';
import PlanView from '../components/PlanView';
import TraceView from '../components/TraceView';
import type {
  PlanStep,
  WorkflowMessage,
  WorkflowRun,
  WorkflowStep,
} from '../types/workflow';

export default function LiveWorkflowPage() {
  const [plan, setPlan] = useState<PlanStep[]>([]);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [workflowRun, setWorkflowRun] = useState<WorkflowRun | null>(null);
  const [status, setStatus] = useState('');
  const eventSourceRef = useRef<EventSource | null>(null);

  const handleStream = (query: string) => {
    eventSourceRef.current?.close();
    let completed = false;

    setStatus('Connecting...');
    setPlan([]);
    setSteps([]);
    setWorkflowRun(null);

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
            setSteps((prev) => {
              const existingStep = prev.find(
                (step) => step.step === msg.data.step,
              );

              if (existingStep) {
                return prev.map((step) =>
                  step.step === msg.data.step
                    ? {
                        ...step,
                        ...msg.data,
                        status: 'running',
                        output: '',
                        tools: [],
                      }
                    : step,
                );
              }

              return [
                ...prev,
                { ...msg.data, status: 'running', output: '', tools: [] },
              ];
            });
            break;

          case 'step_done':
            setSteps((prev) => {
              const existingStep = prev.find(
                (step) => step.step === msg.data.step,
              );

              if (!existingStep) {
                return [
                  ...prev,
                  {
                    step: msg.data.step,
                    description: `Step ${msg.data.step}`,
                    status: 'done',
                    output: msg.data.output,
                    tools: msg.data.tools ?? [],
                  },
                ];
              }

              return prev.map((step) =>
                step.step === msg.data.step
                  ? {
                      ...step,
                      status: 'done',
                      output: msg.data.output,
                      tools: msg.data.tools ?? [],
                    }
                  : step,
              );
            });
            break;

          case 'final':
            completed = true;
            setWorkflowRun(msg.data);
            setStatus(msg.data.status === 'failed' ? 'Failed' : 'Completed');
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

  const completedSteps = steps.filter((step) => step.status === 'done').length;
  const isRunning =
    Boolean(status) &&
    status !== 'Completed' &&
    status !== 'Failed' &&
    status !== 'Stream disconnected';

  const stages = [
    {
      icon: '🧠',
      label: 'Planner',
      detail:
        plan.length > 0
          ? `${plan.length} steps mapped`
          : 'Breaks the request into a strategy',
      tone: status.includes('Planning')
        ? 'active'
        : plan.length > 0
          ? 'done'
          : 'idle',
    },
    {
      icon: '⚙️',
      label: 'Executor',
      detail:
        steps.length > 0
          ? `${completedSteps}/${steps.length} steps finished`
          : 'Runs steps and calls tools',
      tone: status.includes('Executing')
        ? 'active'
        : steps.length > 0 &&
            (Boolean(workflowRun) ||
              status.includes('Reviewing') ||
              status.includes('Evaluating'))
          ? 'done'
          : steps.length > 0
            ? 'active'
            : 'idle',
    },
    {
      icon: '🔍',
      label: 'Reviewer',
      detail:
        workflowRun || status.includes('Evaluating')
          ? 'Final answer synthesized'
          : 'Shapes the response for delivery',
      tone: status.includes('Reviewing')
        ? 'active'
        : workflowRun || status.includes('Evaluating')
          ? 'done'
          : 'idle',
    },
    {
      icon: '📏',
      label: 'Evaluator',
      detail:
        workflowRun?.evaluation_score !== null &&
        workflowRun?.evaluation_score !== undefined
          ? `${workflowRun.evaluation_score}/10 with rationale`
          : workflowRun?.status === 'failed'
            ? 'Skipped after workflow failure'
            : 'Scores the answer and explains why',
      tone: status.includes('Evaluating')
        ? 'active'
        : workflowRun
          ? 'done'
          : 'idle',
    },
  ] as const;

  return (
    <>
      <header className="hero">
        <div className="hero__badge">Portfolio workflow demo</div>
        <div className="hero__content">
          <p className="hero__eyebrow">
            Planner - Executor - Reviewer - Evaluator
          </p>
          <h2>Live workflow trace</h2>
          <p className="hero__lede">
            A process-first interface that shows how the system plans work,
            executes steps, uses tools, and delivers a reviewed and scored
            answer in real time.
          </p>
        </div>
      </header>

      <ChatInput onSubmit={handleStream} isRunning={isRunning} />

      <main className="workspace-grid">
        <section className="workspace-panel">
          <div className="panel-banner">
            <div>
              <p className="panel-banner__eyebrow">Process</p>
              <h2>Live workflow trace</h2>
            </div>

            <p className="panel-banner__copy">
              Follow the plan, execution, and tool usage as the workflow moves
              from intent to answer.
            </p>
          </div>

          <div className="status-board">
            {stages.map((stage) => (
              <article
                key={stage.label}
                className={`stage-card stage-card--${stage.tone}`}
              >
                <p className="stage-card__label">
                  <span>{stage.icon}</span>
                  {stage.label}
                </p>
                <p className="stage-card__detail">{stage.detail}</p>
              </article>
            ))}
          </div>

          <div className="live-status">
            <span
              className={`live-status__dot${isRunning ? ' live-status__dot--active' : ''}`}
            />
            <span>{status || 'Waiting for a workflow request.'}</span>
          </div>

          <PlanView plan={plan} steps={steps} />
          <TraceView steps={steps} />
        </section>

        <section className="workspace-panel workspace-panel--answer">
          <div className="panel-banner panel-banner--answer">
            <div>
              <p className="panel-banner__eyebrow">Result</p>
              <h2>Presentation-ready answer</h2>
            </div>

            <p className="panel-banner__copy">
              The reviewer consolidates every step into a clean, polished final
              response, and the evaluator adds a light-touch quality check.
            </p>
          </div>

          <FinalAnswer workflowRun={workflowRun} status={status} />
        </section>
      </main>
    </>
  );
}
