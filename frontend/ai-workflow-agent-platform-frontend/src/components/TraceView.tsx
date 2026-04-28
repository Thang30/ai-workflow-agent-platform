export default function TraceView({ traces }: any) {
  return (
    <div>
      <h2>Execution</h2>
      {traces.map((t: any) => (
        <div
          key={t.step}
          style={{
            border: '1px solid #ccc',
            margin: '10px',
            padding: '10px',
          }}
        >
          <h3>Step {t.step}</h3>
          <p>
            <strong>{t.description}</strong>
          </p>

          <details>
            <summary>Input</summary>
            <pre>{t.input}</pre>
          </details>

          <details>
            <summary>Output</summary>
            <pre>{t.output}</pre>
          </details>
        </div>
      ))}
    </div>
  );
}
