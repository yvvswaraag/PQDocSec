import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { localPost, localGet } from "../services/api";
import { setPeerApi } from "../config/api";

export default function ReceiverDashboard() {
  const [name, setName] = useState("");
  const [state, setState] = useState("INIT");
  const [ip, setIp] = useState(null);
  const [senderInfo, setSenderInfo] = useState(null);
  const [error, setError] = useState(null);
  const pollIntervalRef = useRef(null);
  const navigate = useNavigate();
  const pqc = "/pqc"
  const startBroadcast = async () => {
    setState("BROADCASTING");
    setError(null);
    
    try {
      const res = await localPost(`${pqc}/receiver/start`, { name });
      setIp(res.ip);
      setState("WAITING");
      
      pollForHandshake();
    } catch (err) {
      console.error("Failed to start broadcasting:", err);
      setState("ERROR");
      setError("Failed to start receiver");
    }
  };

  const pollForHandshake = () => {
    let timeoutId;
    
    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await localGet(`${pqc}/receiver/status`);
        
        if (status.status === "READY") {
          clearInterval(pollIntervalRef.current);
          clearTimeout(timeoutId);
          
          setSenderInfo({
            ip: status.sender_ip,
            port: status.sender_port,
            name: status.sender_name
          });
          
          setState("CONFIRMING");
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 1000);
    
    timeoutId = setTimeout(() => {
      clearInterval(pollIntervalRef.current);
      if (state === "WAITING") {
        setState("ERROR");
        setError("No sender connected within timeout");
      }
    }, 60000);
  };

  const confirmConnection = async () => {
    setState("HANDSHAKING");
    setError(null);
    
    try {
      const result = await localPost(`${pqc}/receiver/acknowledge`, {
        sender_ip: senderInfo.ip,
        sender_port: senderInfo.port,
        receiver_name: name
      });
      
      console.log("Acknowledgment sent:", result);
      
      setPeerApi(senderInfo.ip, senderInfo.port, senderInfo.name);
      
      setState("READY");
      
      // Navigate to download page after a brief moment
      setTimeout(() => {
        navigate("/download-file");
      }, 1500);
    } catch (err) {
      console.error("Acknowledgment failed:", err);
      setState("ERROR");
      setError("Failed to confirm connection");
    }
  };

  const rejectConnection = () => {
    setSenderInfo(null);
    setState("WAITING");
    pollForHandshake();
  };

  const retry = () => {
    setError(null);
    setSenderInfo(null);
    setState("INIT");
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
      <div className="w-full max-w-lg p-8 rounded-xl bg-slate-800 shadow-lg">
        {state === "INIT" && (
          <>
            <h2 className="text-2xl font-bold mb-4">Receiver Setup</h2>
            <input
              className="w-full p-3 rounded bg-slate-700 mb-4 text-white"
              placeholder="Enter your display name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && name.trim() && startBroadcast()}
            />
            <button
              onClick={startBroadcast}
              disabled={!name.trim()}
              className="w-full py-3 rounded bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition"
            >
              Start Broadcasting
            </button>
          </>
        )}

        {state === "BROADCASTING" && (
          <>
            <h2 className="text-xl font-semibold mb-2">Starting…</h2>
            <div className="mt-6 animate-pulse text-indigo-400">
              Initializing receiver...
            </div>
          </>
        )}

        {state === "WAITING" && (
          <>
            <h2 className="text-xl font-semibold mb-2">Broadcasting…</h2>
            <p className="text-slate-400">
              Waiting for sender to connect
            </p>
            <div className="mt-6 animate-pulse text-indigo-400">
              📡 Listening on {ip}:5050
            </div>
          </>
        )}

        {state === "CONFIRMING" && senderInfo && (
          <>
            <h2 className="text-xl font-semibold mb-4">Connection Request</h2>
            <div className="bg-slate-700 p-4 rounded-lg mb-6">
              <p className="text-slate-300 mb-2">
                <span className="font-semibold text-emerald-400">
                  {senderInfo.name}
                </span> wants to connect
              </p>
              <p className="text-sm text-slate-400">
                IP: {senderInfo.ip}:{senderInfo.port}
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={confirmConnection}
                className="flex-1 py-3 rounded bg-emerald-600 hover:bg-emerald-500 font-semibold transition"
              >
                Accept
              </button>
              <button
                onClick={rejectConnection}
                className="flex-1 py-3 rounded bg-red-600 hover:bg-red-500 font-semibold transition"
              >
                Reject
              </button>
            </div>
          </>
        )}

        {state === "HANDSHAKING" && (
          <>
            <h2 className="text-xl font-semibold mb-2">Confirming…</h2>
            <div className="mt-6 animate-pulse text-indigo-400">
              Sending acknowledgment to sender...
            </div>
          </>
        )}

        {state === "READY" && (
          <>
            <h2 className="text-2xl font-bold text-emerald-400 mb-4">
              Connected! ✔
            </h2>
            <div className="bg-slate-700 p-4 rounded-lg mb-4">
              <p className="text-slate-300">
                Ready to receive files from{" "}
                <span className="font-semibold text-emerald-400">
                  {senderInfo?.name}
                </span>
              </p>
            </div>
            <p className="text-sm text-slate-400 text-center animate-pulse">
              Redirecting to download page...
            </p>
          </>
        )}

        {state === "ERROR" && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold text-red-400">Error</h2>
            <p className="text-red-300">⚠ {error}</p>
            <button
              onClick={retry}
              className="w-full py-3 rounded bg-red-600 hover:bg-red-500 font-semibold transition"
            >
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
}