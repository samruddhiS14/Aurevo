import { useState } from "react";
import { captureMilestonePayment } from "../../services/paypalService";
export default function CaptureMilestoneButton({ milestoneId, onSuccess }) {
  const [loading,setLoading] = useState(false); const [error,setError] = useState(""); const [message,setMessage] = useState("");
  const capture = async () => { setLoading(true);setError("");setMessage(""); try { const result = await captureMilestonePayment(milestoneId); setMessage(`PayPal confirmed capture ${result.capture_id || "successfully"}.`); onSuccess?.(); } catch(e) { setError(e.response?.data?.detail || "Capture could not be verified. Check payment history before retrying."); } finally {setLoading(false);} };
  return <div className="space-y-1"><button onClick={capture} disabled={loading} className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{loading ? "Capturing..." : "Capture approved milestone"}</button>{message && <p className="text-xs text-emerald-700">{message}</p>}{error && <p className="text-xs text-red-600">{error}</p>}</div>;
}
