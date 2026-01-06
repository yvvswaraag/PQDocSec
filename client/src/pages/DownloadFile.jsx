import { useState, useEffect, useRef } from "react";
import { localPost } from "../services/api";
import { useNavigate } from "react-router-dom";

export default function DownloadFile() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const pollIntervalRef = useRef(null);
  const failureCountRef = useRef(0);
  const navigate = useNavigate();

  useEffect(() => {
    startPolling();

    return () => {
      stopPolling();
    };
  }, []);

  const startPolling = () => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const result = await localPost("/next-file", {});

        // 204 / 403 → silent wait
        if (!result) {
          setLoading(true);
          return;
        }

        // ✅ File received
        failureCountRef.current = 0;
        setError(null);
        setLoading(false);

        setFiles(prev => [
          ...prev,
          {
            id: result.id,
            filename: result.filename,
            fileData: result.file_data,
            fileSize: result.file_size
          }
        ]);

      } catch (err) {
        console.warn("Polling issue:", err);

        failureCountRef.current += 1;

        // Only show error after repeated failures
        if (failureCountRef.current >= 3) {
          setError("Connection temporarily unavailable");
          setLoading(false);
        }
      }
    }, 20000); // ⏱ Poll every 5 seconds
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const downloadFile = (file) => {
    try {
      stopPolling();

      // Decode base64
      const binary = atob(file.fileData);
      const bytes = new Uint8Array(binary.length);

      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }

      const blob = new Blob([bytes], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();

      URL.revokeObjectURL(url);
      document.body.removeChild(a);

      // Navigate after download
      navigate("/filedownload");

    } catch (err) {
      console.error("Download failed:", err);
      setError("Download failed");
    }
  };

  const retryConnection = () => {
    setError(null);
    setLoading(true);
    failureCountRef.current = 0;
    stopPolling();
    startPolling();
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">

        {/* Header */}
        <div className="mb-8 text-center">
          <button
            onClick={() => navigate("/receiver")}
            className="mb-4 text-slate-400 hover:text-white"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold">Receive Documents</h1>
          <p className="text-slate-400">Listening for incoming files…</p>
        </div>

        {/* Error (only after repeated failures) */}
        

        {/* Waiting */}
        {loading && files.length === 0 && !error && (
          <div className="bg-slate-800 p-10 rounded-xl text-center">
            <span className="text-6xl animate-pulse">📥</span>
            <p className="mt-4 text-slate-400">Waiting for files…</p>
            {/* <p className="mt-2 text-xs text-slate-500">Polling every 5 seconds</p> */}
          </div>
        )}

        {/* Files */}
        {files.length > 0 && (
          <div className="bg-slate-800 rounded-xl p-6 space-y-4">
            {files.map(file => (
              <div
                key={file.id}
                className="bg-slate-700 p-4 rounded-lg flex justify-between items-center"
              >
                <div>
                  <p className="font-semibold">{file.filename}</p>
                  <p className="text-sm text-slate-400">
                    {(file.fileSize / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <p className="text-xs text-emerald-400">✓ Decrypted & Ready</p>
                </div>

                <button
                  onClick={() => downloadFile(file)}
                  className="bg-emerald-600 px-4 py-2 rounded-lg hover:bg-emerald-500"
                >
                  Download
                </button>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}