import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { localPost, localGet } from "../services/api";
import { setPeerApi, setSelfName } from "../config/api";

export default function SenderDashboard() {
  const [state, setState] = useState("START");
  const [name, setName] = useState("");
  const [receiver, setReceiver] = useState(null);
  const [error, setError] = useState(null);
  const pollIntervalRef = useRef(null);
  const navigate = useNavigate();
  const pqc = "/pqc";
  const startSender = () => {
    if (name.trim()) {
      setSelfName(name);
      setState("INIT");
    }
  };

  const discover = async () => {
    setState("SEARCHING");
    setError(null);
    
    try {
      const res = await localPost(`${pqc}/sender/discover`);
      
      if (!res.receiver_ip || !res.receiver_port) {
        throw new Error("Invalid receiver data: missing IP or port");
      }
      
      setPeerApi(res.receiver_ip, res.receiver_port, res.receiver_name);
      console.log("Set peer API to:", res.receiver_ip, res.receiver_port, res.receiver_name);
      
      setReceiver(res);
      setState("FOUND");
    } catch (err) {
      console.error("Discovery failed:", err);
      setState("ERROR");
      setError(err.message || "No receiver found");
    }
  };

  const handshake = async () => {
    setState("HANDSHAKING");
    setError(null);
    
    try {
      const result = await localPost(`${pqc}/sender/handshake`, {
        receiver_ip: receiver.receiver_ip,
        receiver_port: receiver.receiver_port,
        sender_name: name
      });
      
      console.log("Handshake sent:", result);
      setState("WAITING_ACK");
      
      // Start polling for acknowledgment
      pollForAcknowledgment();
    } catch (err) {
      console.error("Handshake failed:", err);
      setState("ERROR");
      setError("Handshake failed. Please try again.");
    }
  };

  const pollForAcknowledgment = () => {
    let timeoutId;
    
    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await localGet(`${pqc}/sender/ack_status`);
        
        if (status.status === "ACKNOWLEDGED") {
          clearInterval(pollIntervalRef.current);
          clearTimeout(timeoutId);
          
          setState("READY");
          
          // Navigate to upload page after a brief moment
          setTimeout(() => {
            navigate("/upload-file");
          }, 1500);
        }
      } catch (err) {
        console.error("Polling acknowledgment error:", err);
      }
    }, 1000);
    
    // Timeout after 30 seconds
    timeoutId = setTimeout(() => {
      clearInterval(pollIntervalRef.current);
      if (state === "WAITING_ACK") {
        setState("ERROR");
        setError("Receiver did not acknowledge connection");
      }
    }, 30000);
  };

  const retry = () => {
    setError(null);
    setReceiver(null);
    setState("INIT");
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center">
      {/* Name Input Screen */}
      {state === "START" && (
        <div className="w-full max-w-md px-6">
          <h2 className="text-2xl font-bold mb-4 text-center">Sender Setup</h2>
          <input
            className="w-full p-3 rounded bg-slate-700 mb-4 text-white"
            placeholder="Enter your display name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && startSender()}
          />
          <button
            onClick={startSender}
            disabled={!name.trim()}
            className="w-full py-3 rounded bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-600 disabled:cursor-not-allowed transition"
          >
            Continue
          </button>
        </div>
      )}

      {/* Radar (only show when not in START state) */}
      {state !== "START" && (
        <>
          <div className="relative w-72 h-72 rounded-full bg-slate-800 border border-emerald-400 shadow-lg overflow-hidden">
            {/* Grid */}
            <div className="absolute inset-0 rounded-full border border-emerald-700 opacity-30" />

            {/* Pulsing rings for SEARCHING */}
            {state === "SEARCHING" && (
              <>
                <div className="absolute inset-0 rounded-full border-2 border-emerald-500 animate-ping opacity-20" />
                <div className="absolute inset-6 rounded-full border border-emerald-500 opacity-30" />
                <div className="absolute inset-12 rounded-full border border-emerald-500 opacity-30" />
              </>
            )}

            {/* Sweep for SEARCHING */}
            {state === "SEARCHING" && (
              <div className="absolute inset-0 origin-center animate-spin-slow">
                <div className="absolute top-1/2 left-1/2 w-1/2 h-1 bg-gradient-to-r from-emerald-400 to-transparent" />
              </div>
            )}

            {/* Receiver dot for FOUND */}
            {state === "FOUND" && (
              <button
                onClick={handshake}
                disabled={state === "HANDSHAKING" || state === "READY"}
                className="absolute top-[30%] left-[65%] flex flex-col items-center group"
              >
                <div className="w-14 h-14 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg group-hover:scale-105 transition">
                  <span className="text-xl">👤</span>
                </div>
                <span className="mt-2 text-sm text-emerald-300">
                  {receiver?.receiver_name || "Receiver"}
                </span>
              </button>
            )}

            {/* Connection Bridge Animation for WAITING_ACK */}
            {state === "WAITING_ACK" && (
              <>
                {/* Sender (left side) */}
                <div className="absolute top-1/2 left-[15%] -translate-y-1/2 flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-indigo-500 flex items-center justify-center shadow-lg">
                    <span className="text-lg">📱</span>
                  </div>
                  <span className="mt-1 text-xs text-indigo-300">You</span>
                </div>

                {/* Receiver (right side) */}
                <div className="absolute top-1/2 right-[15%] -translate-y-1/2 flex flex-col items-center">
                  <div className="w-12 h-12 rounded-full bg-emerald-500 flex items-center justify-center shadow-lg">
                    <span className="text-lg">💻</span>
                  </div>
                  <span className="mt-1 text-xs text-emerald-300">
                    {receiver?.receiver_name}
                  </span>
                </div>

                {/* Animated connection particles */}
                <div className="absolute top-1/2 left-[25%] right-[25%] h-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-500 opacity-50" />
                
                {/* Traveling particles */}
                <div className="absolute top-1/2 left-[25%] w-3 h-3 bg-indigo-400 rounded-full animate-travel-right" />
                <div className="absolute top-1/2 right-[25%] w-3 h-3 bg-emerald-400 rounded-full animate-travel-left" />
                
                {/* Pulse effect */}
                <div className="absolute inset-0 border-2 border-purple-500 rounded-full animate-pulse opacity-20" />
              </>
            )}

            {/* Success checkmark for READY */}
            {state === "READY" && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-20 h-20 rounded-full bg-emerald-500 flex items-center justify-center shadow-xl animate-scale-in">
                  <span className="text-4xl">✓</span>
                </div>
              </div>
            )}

            {/* Center dot */}
            <div className="absolute inset-1/2 w-3 h-3 bg-emerald-400 rounded-full -translate-x-1/2 -translate-y-1/2" />
          </div>

          {/* Status */}
          <div className="mt-8 text-center">
            {state === "INIT" && (
              <button
                onClick={discover}
                className="px-6 py-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 font-semibold transition"
              >
                Start Scan
              </button>
            )}

            {state === "SEARCHING" && (
              <p className="text-emerald-400 tracking-wide">
                Scanning network for receivers…
              </p>
            )}

            {state === "FOUND" && (
              <p className="text-emerald-400 font-semibold">
                Receiver found: {receiver.receiver_ip}
              </p>
            )}

            {state === "HANDSHAKING" && (
              <p className="text-indigo-400 animate-pulse">
                Sending connection request…
              </p>
            )}

            {state === "WAITING_ACK" && (
              <div className="space-y-2">
                <p className="text-purple-400 font-semibold animate-pulse">
                  Waiting for receiver to accept…
                </p>
                <p className="text-sm text-slate-400">
                  {receiver?.receiver_name} needs to confirm the connection
                </p>
              </div>
            )}

            {state === "READY" && (
              <div className="space-y-2">
                <p className="text-green-400 font-bold text-lg">
                  Connection established! ✔
                </p>
                <p className="text-sm text-slate-400">
                  Redirecting to upload...
                </p>
              </div>
            )}

            {state === "ERROR" && (
              <div className="space-y-4">
                <p className="text-red-400 font-semibold">
                  ⚠ {error}
                </p>
                <button
                  onClick={retry}
                  className="px-6 py-3 rounded-lg bg-red-600 hover:bg-red-500 font-semibold transition"
                >
                  Try Again
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}