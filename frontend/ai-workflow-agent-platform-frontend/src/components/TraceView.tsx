export default function StepList({ steps }: any) {
  return (
    <div className="card">
      <h2>⚙️ Execution</h2>

      {steps.map((s: any) => (
        <div
          key={s.step}
          style={{
            marginBottom: '12px',
            padding: '12px',
            borderRadius: '10px',
            background: s.status === 'running' ? '#1e40af' : '#065f46',
            transition: 'all 0.3s',
          }}
        >
          <strong>
            Step {s.step}: {s.description}
          </strong>

          <p style={{ marginTop: '5px', opacity: 0.8 }}>
            {s.status === 'running' ? '⏳ Running...' : '✅ Done'}
          </p>

          {s.output && <pre style={{ marginTop: '10px' }}>{s.output}</pre>}
        </div>
      ))}
    </div>
  );
}
