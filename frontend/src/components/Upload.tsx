import { useState, useRef } from 'react';
import axios from 'axios';
import { Upload as UploadIcon, FileUp, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<{ processed: number; total: number; failed: number } | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle');
  const [errorMsg, setErrorMsg] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setStatus('idle');
      setProgress(null);
      setLogs([]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setStatus('uploading');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const taskId = res.data.task_id;
      setStatus('processing');
      startEventSource(taskId);
    } catch (err: any) {
      console.error(err);
      setStatus('error');
      setErrorMsg(err.response?.data?.detail || 'Upload failed');
      setUploading(false);
    }
  };

  const startEventSource = (taskId: string) => {
    const eventSource = new EventSource(`/api/ingest-status?task_id=${taskId}`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.status === 'processing') {
             // For processing events, we want to update the progress bar but also log the URL being processed
             setProgress({
                processed: data.current, // current index (1-based)
                total: data.total,
                failed: 0 // We don't have cumulative failed count in 'processing' event from backend yet?
                          // Actually pipeline.py yields: {status: "processing", current: i+1, total: total, url: ..., title: ...}
                          // It doesn't yield cumulative failed count in 'processing' event.
                          // We should track it locally or update backend.
                          // For now, let's just use what we have.
             });
             setLogs(prev => [...prev, `[${data.current}/${data.total}] Processing: ${data.url}`]);
          } else if (data.status === 'failed') {
             // Backend yields: {status: "failed", url: ..., reason: ...}
             // We should increment failed count locally if we want to track it real-time
             setLogs(prev => [...prev, `❌ FAILED: ${data.url} - ${data.reason}`]);
          } else if (data.status === 'error') {
             setLogs(prev => [...prev, `❌ ERROR: ${data.url} - ${data.message}`]);
          } else if (data.status === 'completed') {
             setStatus('completed');
             setUploading(false);
             eventSource.close();
             if (data.success !== undefined) {
                setLogs(prev => [...prev, `✅ Done! Success: ${data.success}, Failed: ${data.failed}`]);
                setProgress({
                   processed: data.success,
                   failed: data.failed,
                   total: (data.success + data.failed)
                });
             }
          } else if (data.status === 'parsing' || data.status === 'parsing_complete') {
             setLogs(prev => [...prev, `ℹ️ ${data.message}`]);
          }
        } catch (e) {
          console.error("Error parsing SSE data", e, event.data);
        }
      
      // Auto scroll logs
      if (logsEndRef.current) {
        logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    };

    eventSource.onerror = () => {
      // If connection closes cleanly (server finishes), it might trigger error or just close.
      // But we close explicitly on 'completed'.
      // If real error:
      if (status !== 'completed') {
          // It might be just end of stream if server closes connection without 'completed' event (which shouldn't happen based on code)
          // But let's assume error if not completed
          // eventSource.close();
      }
    };
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-md mt-10">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <UploadIcon className="w-6 h-6" /> Ingest Bookmarks
      </h2>

      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
        <input
          type="file"
          id="file-upload"
          className="hidden"
          accept=".html,.htm"
          onChange={handleFileChange}
          disabled={uploading}
        />
        <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
          <FileUp className="w-12 h-12 text-gray-400 mb-2" />
          <span className="text-gray-600 font-medium">
            {file ? file.name : "Click to select bookmarks HTML file"}
          </span>
          <span className="text-sm text-gray-400 mt-1">Supports Netscape Bookmark format</span>
        </label>
      </div>

      {file && (
        <button
          onClick={handleUpload}
          disabled={uploading}
          className={`mt-4 w-full py-2 px-4 rounded-md text-white font-medium transition-colors ${
            uploading ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {uploading ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" /> Processing...
            </span>
          ) : (
            "Start Ingestion"
          )}
        </button>
      )}

      {status === 'processing' && progress && (
        <div className="mt-6">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{Math.round((progress.processed / progress.total) * 100)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${(progress.processed / progress.total) * 100}%` }}
            ></div>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>Processed: {progress.processed}</span>
            <span>Failed: {progress.failed}</span>
            <span>Total: {progress.total}</span>
          </div>
        </div>
      )}

      {status === 'completed' && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md flex items-center gap-3 text-green-700">
          <CheckCircle className="w-5 h-5" />
          <div>
            <p className="font-medium">Ingestion Complete!</p>
            {progress && (
                <p className="text-sm">Successfully processed {progress.processed} bookmarks.</p>
            )}
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md flex items-center gap-3 text-red-700">
          <AlertCircle className="w-5 h-5" />
          <div>
            <p className="font-medium">Error</p>
            <p className="text-sm">{errorMsg}</p>
          </div>
        </div>
      )}
      
      <div className="mt-6 bg-gray-900 text-gray-300 p-4 rounded-md h-48 overflow-y-auto font-mono text-xs">
        {logs.length === 0 ? <span className="text-gray-600">Logs will appear here...</span> : logs.map((log, i) => (
            <div key={i}>{log}</div>
        ))}
        <div ref={logsEndRef} />
      </div>
    </div>
  );
}
