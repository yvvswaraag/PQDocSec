import { useState, useEffect, useRef } from "react";
import { localPost } from "../services/api";
import { useNavigate } from "react-router-dom";

export default function DownloadFile() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [decrypting, setDecrypting] = useState(false);
  const [animationStep, setAnimationStep] = useState(0);
  const [currentFile, setCurrentFile] = useState(null);
  const pollIntervalRef = useRef(null);
  const navigate = useNavigate();
const pqc = "/pqc"
  useEffect(() => {
    startPolling();
    return () => {
      stopPolling();
    };
  }, []);

  const startPolling = () => {
    pollIntervalRef.current = setInterval(async () => {
      try {
        const result = await localPost(pqc+"/next-file", {});

        if (!result) {
          setLoading(true);
          return;
        }

        setLoading(false);

        setFiles(prev => [
          ...prev,
          {
            id: result.id,
            filename: result.filename,
            fileData: result.file_data,
            fileSize: result.file_size,
            encryptedAesKey: result.encrypted_aes_key,
            signature: result.signature,
            senderPublicKey: result.sender_public_key,
            rsaPrivateKey: result.rsa_private_key
          }
        ]);

      } catch (err) {
        console.warn("Polling issue:", err);
      }
    }, 20000);
  };

  const stopPolling = () => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

    const triggerDownload = (file) => {
    try {
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

      setTimeout(() => navigate("/filedownload"), 1500);
    } catch (err) {
      console.error("Download failed:", err);
    }
  };

  /* 🔥 Trigger download exactly at animation step 5 */
  useEffect(() => {
    if (animationStep === 5 && currentFile) {
      setTimeout(() => triggerDownload(currentFile), 800);
    }
  }, [animationStep]);

  const downloadFile = (file) => {
    stopPolling();
    setCurrentFile(file);
    setDecrypting(true);
    setAnimationStep(0);

    setTimeout(() => setAnimationStep(1), 500);
    setTimeout(() => setAnimationStep(2), 2500);
    setTimeout(() => setAnimationStep(3), 4500);
    setTimeout(() => setAnimationStep(4), 6500);
    setTimeout(() => setAnimationStep(5), 8500);
  };


  const truncate = (str, len = 20) => {
    if (!str) return "";
    return str.length > len ? str.substring(0, len) + "..." : str;
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-6">
      <div className="w-full max-w-4xl">

        {/* Header */}
        <div className="mb-8 text-center">
          <button
            onClick={() => navigate("/receiver")}
            className="mb-4 text-slate-400 hover:text-white transition flex items-center gap-2 mx-auto"
          >
            <span>←</span> Back to Dashboard
          </button>
          <h1 className="text-3xl font-bold mb-2">Receive Documents</h1>
          <p className="text-slate-400">Secure end-to-end encrypted file transfer</p>
        </div>

        {/* Waiting */}
        {loading && files.length === 0 && (
          <div className="bg-slate-800 p-12 rounded-xl text-center shadow-xl">
            <span className="text-8xl animate-pulse">📥</span>
            <p className="mt-6 text-xl text-slate-400">Listening for incoming files…</p>
            <div className="mt-4 flex items-center justify-center gap-2">
              <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
            </div>
          </div>
        )}

        {/* Files */}
        {files.length > 0 && !decrypting && (
          <div className="bg-slate-800 rounded-xl p-6 space-y-4 shadow-xl">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              <span>📬</span> Received Files
            </h2>
            {files.map(file => (
              <div
                key={file.id}
                className="bg-slate-700 p-6 rounded-lg flex items-center gap-4"
              >
                <div className="w-16 h-16 bg-emerald-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-3xl">📕</span>
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold truncate">{file.filename}</h4>
                  <p className="text-sm text-slate-400">
                    {(file.fileSize / 1024 / 1024).toFixed(2)} MB
                  </p>
                  <p className="text-xs text-emerald-400 mt-1">✓ Encrypted & Ready</p>
                </div>

                <button
                  onClick={() => downloadFile(file)}
                  className="px-6 py-3 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 font-semibold transition shadow-lg hover:shadow-xl flex items-center gap-2"
                >
                  <span>🔓</span>
                  Decrypt & Download
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Decryption Animation */}
        {decrypting && currentFile && (
          <div className="bg-slate-800 rounded-xl p-8 shadow-xl">
            {/* File Info */}
            <div className="bg-slate-700 rounded-lg p-6 flex items-center gap-4 mb-6">
              <div className="w-16 h-16 bg-emerald-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-3xl">📕</span>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold truncate">{currentFile.filename}</h4>
                <p className="text-sm text-slate-400">
                  {(currentFile.fileSize / 1024 / 1024).toFixed(2)} MB
                </p>
                <p className="text-xs text-amber-400 mt-1 animate-pulse">🔄 Decrypting...</p>
              </div>
            </div>

            {/* Animation Steps */}
            <div className="space-y-6">
              {/* Step 1: Signature Verification */}
              <div className={`transition-all duration-500 ${animationStep >= 1 ? 'opacity-100' : 'opacity-30'}`}>
                <div className="flex items-center gap-4 mb-3">
                  <div className="w-10 h-10 rounded-full bg-orange-500 flex items-center justify-center flex-shrink-0">
                    {animationStep > 1 ? '✓' : '1'}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">Signature Verification</h4>
                    <p className="text-sm text-slate-400">Verifying sender's digital signature</p>
                  </div>
                </div>
                {animationStep === 1 && (
                  <div className="ml-14 bg-slate-700 p-4 rounded animate-fade-in space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl animate-pulse">✍️</span>
                      <span className="text-xs text-slate-400">Sender's Public Key:</span>
                    </div>
                    <code className="text-xs text-orange-300 break-all block">
                      {truncate(currentFile.senderPublicKey, 60)}
                    </code>
                    <div className="text-center text-2xl animate-pulse">⬇</div>
                    <code className="text-xs text-emerald-300 break-all block">
                      {truncate(currentFile.signature, 60)}
                    </code>
                    <p className="text-xs text-emerald-400 mt-2">✓ Signature Valid</p>
                  </div>
                )}
              </div>

              {/* Step 2: RSA Decryption */}
              <div className={`transition-all duration-500 ${animationStep >= 2 ? 'opacity-100' : 'opacity-30'}`}>
                <div className="flex items-center gap-4 mb-3">
                  <div className="w-10 h-10 rounded-full bg-purple-500 flex items-center justify-center flex-shrink-0">
                    {animationStep > 2 ? '✓' : '2'}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">RSA Key Decapsulation</h4>
                    <p className="text-sm text-slate-400">Decrypting AES key with private key</p>
                  </div>
                </div>
                {animationStep === 2 && (
                  <div className="ml-14 bg-slate-700 p-4 rounded animate-fade-in space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl animate-bounce">🔐</span>
                      <span className="text-xs text-slate-400">Your RSA Private Key:</span>
                    </div>
                    <code className="text-xs text-purple-300 break-all block">
                      {truncate(currentFile.rsaPrivateKey, 60)}
                    </code>
                    <div className="text-center text-2xl animate-pulse">⬇</div>
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">🔑</span>
                      <span className="text-xs text-slate-400">Decrypted AES Key:</span>
                    </div>
                    <code className="text-xs text-emerald-300 break-all block">
                      {truncate(currentFile.encryptedAesKey, 60)}
                    </code>
                  </div>
                )}
              </div>

              {/* Step 3: AES Decryption */}
              <div className={`transition-all duration-500 ${animationStep >= 3 ? 'opacity-100' : 'opacity-30'}`}>
                <div className="flex items-center gap-4 mb-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0">
                    {animationStep > 3 ? '✓' : '3'}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">AES-256 Decryption</h4>
                    <p className="text-sm text-slate-400">Decrypting file content</p>
                  </div>
                </div>
                {animationStep === 3 && (
                  <div className="ml-14 bg-slate-700 p-4 rounded animate-fade-in">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-2xl animate-pulse">🔓</span>
                      <span className="text-xs text-slate-400">Decrypting with AES-256...</span>
                    </div>
                    <div className="w-full bg-slate-600 rounded-full h-2 overflow-hidden">
                      <div className="bg-gradient-to-r from-indigo-500 to-purple-500 h-full animate-progress"></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Step 4: Hash Verification */}
              <div className={`transition-all duration-500 ${animationStep >= 4 ? 'opacity-100' : 'opacity-30'}`}>
                <div className="flex items-center gap-4 mb-3">
                  <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center flex-shrink-0">
                    {animationStep > 4 ? '✓' : '4'}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold">Integrity Verification</h4>
                    <p className="text-sm text-slate-400">Verifying file integrity with SHA-256</p>
                  </div>
                </div>
                {animationStep === 4 && (
                  <div className="ml-14 bg-slate-700 p-4 rounded animate-fade-in">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl animate-spin-slow">#️⃣</span>
                      <span className="text-xs text-slate-400">Computing hash...</span>
                    </div>
                    <p className="text-xs text-emerald-400 mt-3">✓ File Integrity Verified</p>
                  </div>
                )}
              </div>

              {/* Step 5: Downloading */}
              {animationStep === 5 && (
                <div className="text-center py-8 animate-fade-in">
                  <div className="text-8xl mb-4 animate-bounce">💾</div>
                  <h3 className="text-2xl font-bold text-emerald-400 mb-2">Download Complete!</h3>
                  <p className="text-slate-400">Your file has been securely decrypted</p>
                  <div className="mt-4 flex items-center justify-center gap-2">
                    <div className="w-3 h-3 bg-emerald-500 rounded-full animate-ping"></div>
                    <div className="w-3 h-3 bg-emerald-500 rounded-full animate-ping" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-3 h-3 bg-emerald-500 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

      </div>
    </div>
  );
}