import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type FinalAnswerProps = {
  answer: string;
};

export default function FinalAnswer({ answer }: FinalAnswerProps) {
  return (
    <div className="card">
      <h2>✅ Final Answer</h2>
      <div className="markdown-body">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
      </div>
    </div>
  );
}
