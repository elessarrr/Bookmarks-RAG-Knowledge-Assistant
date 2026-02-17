import { useState } from 'react';
import Upload from './components/Upload';
import Chat from './components/Chat';
import { BookMarked, MessageSquare, Upload as UploadIcon } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState<'upload' | 'chat'>('upload');

  // We lift state up to persist the chat component when switching tabs, 
  // or simply use CSS to hide/show instead of conditional rendering.
  // Using CSS display: none is the easiest way to preserve state.

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans text-gray-900">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookMarked className="w-6 h-6 text-blue-600" />
            <h1 className="text-xl font-bold tracking-tight">Bookmarks RAG Knowledge Assistant</h1>
          </div>
          
          <nav className="flex gap-1 bg-gray-100 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'upload'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
              }`}
            >
              <UploadIcon className="w-4 h-4" /> Manage
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === 'chat'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
              }`}
            >
              <MessageSquare className="w-4 h-4" /> Chat
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
          
          <div style={{ display: activeTab === 'upload' ? 'block' : 'none' }}>
              <div className="mb-8 text-center">
                <h2 className="text-3xl font-bold text-gray-900">Manage Your Knowledge Base</h2>
                <p className="mt-2 text-gray-600">Upload your bookmark exports to start chatting with your saved content.</p>
              </div>
              <Upload />
          </div>

          <div style={{ display: activeTab === 'chat' ? 'block' : 'none' }}>
              <div className="mb-4 text-center">
                 <h2 className="text-3xl font-bold text-gray-900">Chat with Bookmarks</h2>
                 <p className="mt-2 text-gray-600">Ask questions and get answers based on your saved pages.</p>
              </div>
              <Chat />
          </div>

        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-6 mt-auto">
        <div className="max-w-5xl mx-auto px-4 text-center text-sm text-gray-500">
          <p>Local-first Bookmarks RAG Knowledge Assistant. Powered by DuckDB, Ollama & React.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;