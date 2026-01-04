import { useState } from "react";
import { localPost } from "../services/api";

export default function ReceiverDashboard() {
  const [name, setName] = useState("");
  const [state, setState] = useState("INIT");
  const [ip, setIp] = useState(null);

  const startBroadcast = async () => {
    setState("BROADCASTING");
    const res = await localPost("/receiver/start", { name });
    setIp(res.ip);
    setState("WAITING"); // waiting for handshake
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
      <div className="w-full max-w-lg p-8 rounded-xl bg-slate-800 shadow-lg">
        {state === "INIT" && (
          <>
            <h2 className="text-2xl font-bold mb-4">Receiver Setup</h2>
            <input
              className="w-full p-3 rounded bg-slate-700 mb-4"
              placeholder="Enter your display name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <button
              onClick={startBroadcast}
              disabled={!name}
              className="w-full py-3 rounded bg-indigo-600 hover:bg-indigo-500"
            >
              Start Broadcasting
            </button>
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

        {state === "READY" && (
          <h2 className="text-2xl font-bold text-emerald-400">
            Handshake complete. Ready to receive files.
          </h2>
        )}
      </div>
    </div>
  );
}
