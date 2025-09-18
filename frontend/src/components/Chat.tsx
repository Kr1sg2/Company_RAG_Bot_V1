import { useState, useRef } from 'react';
import { chat, type ChatRequest, type ChatResponse, type ChatSource } from '../lib/api';

// Local storage key for persisting recent questions
const RECENT_QUESTIONS_KEY = 'chat-recent-questions';

export default function Chat() {
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [recentQuestions, setRecentQuestions] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem(RECENT_QUESTIONS_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const saveRecentQuestion = (question: string) => {
    const trimmed = question.trim();
    if (!trimmed) return;

    const updated = [trimmed, ...recentQuestions.filter(q => q !== trimmed)].slice(0, 3);
    setRecentQuestions(updated);
    try {
      localStorage.setItem(RECENT_QUESTIONS_KEY, JSON.stringify(updated));
    } catch {
      // Ignore localStorage errors
    }
  };

  const handleSubmit = async () => {
    if (!message.trim() || isLoading) return;

    const currentMessage = message.trim();
    setMessage('');
    setError(null);
    setResponse(null);
    setIsLoading(true);

    // Save to recent questions
    saveRecentQuestion(currentMessage);

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const chatRequest: ChatRequest = { message: currentMessage };
      const result = await chat(chatRequest, abortControllerRef.current.signal);
      setResponse(result);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was aborted, don't show error
        return;
      }
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleAbort = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleRecentQuestionClick = (question: string) => {
    setMessage(question);
  };

  return (
    <div className="max-w-2xl mx-auto p-4 space-y-4">
      <h2 className="text-xl font-semibold">Chat Interface</h2>
      
      {/* Recent Questions */}
      {recentQuestions.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-700">Recent questions:</h3>
          <div className="flex flex-wrap gap-2">
            {recentQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleRecentQuestionClick(question)}
                className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full border"
                disabled={isLoading}
              >
                {question.length > 50 ? `${question.slice(0, 50)}...` : question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="space-y-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your question and press Enter to send (Shift+Enter for new line)"
          className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={3}
          disabled={isLoading}
        />
        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={!message.trim() || isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Sending...' : 'Ask'}
          </button>
          {isLoading && (
            <button
              onClick={handleAbort}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
            >
              Abort
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
          Error: {error}
        </div>
      )}

      {/* Response Display */}
      {response && (
        <div className="space-y-3">
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <h3 className="font-medium mb-2">Response:</h3>
            <p className="whitespace-pre-wrap">{response.answer}</p>
          </div>

          {/* Sources */}
          {response.sources && response.sources.length > 0 && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-medium mb-2">Sources:</h4>
              <ul className="space-y-1">
                {response.sources.map((source: ChatSource, index: number) => (
                  <li key={index} className="text-sm">
                    {source.url ? (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 underline"
                      >
                        {source.title || source.url}
                      </a>
                    ) : (
                      <span>{source.title || 'Unknown source'}</span>
                    )}
                    {source.snippet && (
                      <div className="ml-2 text-gray-600 italic">
                        {source.snippet}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}