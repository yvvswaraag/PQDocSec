import { useState } from "react";
import { localPost } from "../services/api";
import { useNavigate } from "react-router-dom";


export default function RoleSelector({ onRoleSelected }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const pqc = "/pqc";
  const selectRole = async (role) => {
    try {
      setLoading(true);
      await localPost(`${pqc}/role/select`, { "role":role });

      const upper = role.toUpperCase();
      onRoleSelected(upper);

      navigate(upper === "SENDER" ? "/sender" : "/receiver");
    } catch {
      alert("Failed to select role");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <div className="w-full max-w-md p-8 rounded-2xl bg-slate-900 shadow-xl border border-slate-700">
        <h1 className="text-3xl font-bold text-center mb-2">
          Secure File Transfer
        </h1>
        <p className="text-slate-400 text-center mb-8">
          Choose your role to begin
        </p>

        <div className="space-y-4">
          <button
            onClick={() => selectRole("sender")}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 transition-all font-semibold text-lg disabled:opacity-50"
          >
            📤 Act as Sender
          </button>

          <button
            onClick={() => selectRole("receiver")}
            disabled={loading}
            className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 transition-all font-semibold text-lg disabled:opacity-50"
          >
            📥 Act as Receiver
          </button>
        </div>

        {loading && (
          <p className="mt-6 text-center text-slate-400">
            Initializing cryptographic keys…
          </p>
        )}
      </div>
    </div>
  );
}
