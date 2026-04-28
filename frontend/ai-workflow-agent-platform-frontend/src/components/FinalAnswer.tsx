export default function FinalAnswer({ answer }: any) {
  return (
    <div className="card">
      <h2>✅ Final Answer</h2>
      <p style={{ lineHeight: '1.6' }}>{answer}</p>
    </div>
  );
}
