import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, User, Bot, ExternalLink, Loader2 } from 'lucide-react';

interface Source {
  url: string;
  title: string;
  score: number;
  text: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

export default function Chat() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMessage = query.trim();
    setQuery('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const res = await axios.post('/api/query', { question: userMessage, k: 5 });
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: res.data.answer,
        sources: res.data.sources
      }]);
    } catch (err: any) {
      console.error(err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: "Sorry, I encountered an error while processing your request. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-4xl mx-auto bg-white rounded-lg shadow-md border border-gray-200 mt-4">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50 rounded-t-lg">
        <h2 className="text-lg font-semibold flex items-center gap-2 text-gray-700">
          <Bot className="w-5 h-5" /> RAG Chat
        </h2>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Ask me anything about your bookmarks!</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
            )}
            
            <div className={`max-w-[80%] rounded-lg p-3 ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-100 text-gray-800'
            }`}>
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
              
              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-4 pt-3 border-t border-gray-200/50">
                  <p className="text-xs font-semibold mb-2 opacity-70 flex items-center gap-1">
                    <ExternalLink className="w-3 h-3" /> Sources:
                  </p>
                  <ul className="space-y-1">
                    {msg.sources.map((source, sIdx) => (
                      <li key={sIdx} className="text-xs bg-white/50 rounded px-2 py-1">
                        <a 
                          href={source.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="hover:underline text-blue-500 truncate block font-medium"
                          title={source.url}
                        >
                          {source.title || source.url}
                        </a>
                        <span className="text-gray-500 text-[10px]">Score: {source.score.toFixed(3)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-gray-600" />
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div className="flex gap-3 justify-start">
             <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                <Bot className="w-5 h-5 text-blue-600" />
              </div>
              <div className="bg-gray-100 rounded-lg p-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-gray-500" />
                <span className="text-sm text-gray-500">Thinking...</span>
              </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-white rounded-b-lg">
        <form onSubmit={handleQuery} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search your bookmarks..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className={`px-4 py-2 rounded-lg text-white transition-colors flex items-center gap-2 ${
              loading || !query.trim() 
                ? 'bg-blue-300 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}