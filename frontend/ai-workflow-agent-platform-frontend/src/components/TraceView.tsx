export default function TraceView({ traces }: any) {
  return (
    <div className="card">
      <h2>⚙️ Execution</h2>

      {traces.map((t: any) => (
        <div
          key={t.step}
          style={{
            borderTop: '1px solid #334155',
            paddingTop: '10px',
            marginTop: '10px',
          }}
        >
          <h3>Step {t.step}</h3>
          <p style={{ opacity: 0.8 }}>{t.description}</p>

          <details>
            <summary style={{ cursor: 'pointer', marginTop: '5px' }}>
              Show details
            </summary>

            <div style={{ marginTop: '10px' }}>
              <strong>Input:</strong>
              <pre>{t.input}</pre>

              <strong>Output:</strong>
              <pre>{t.output}</pre>
            </div>
          </details>
        </div>
      ))}
    </div>
  );
}
