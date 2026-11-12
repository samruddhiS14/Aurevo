import { useCallback, useEffect, useState } from "react";
import { Activity, CheckCircle2, CircleAlert, LoaderCircle, Server, Database, RefreshCw } from "lucide-react";
import { getBackendHealth } from "../services/healthService";

export default function HomePage() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const checkConnection = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setHealth(await getBackendHealth());
    } catch (err) {
      setHealth(null);
      setError(
        err.response?.data?.detail?.message ||
        "Could not reach the backend. Confirm FastAPI and PostgreSQL are running."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { checkConnection(); }, [checkConnection]);

  const connected = health?.status === "ok" && health?.database === "connected";

  return (
    <section className="grid min-h-[68vh] items-center gap-10 py-10 lg:grid-cols-[1.1fr_0.9fr]">
      <div className="max-w-2xl">
        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-brand-100 bg-white/75 px-3 py-1.5 text-xs font-semibold text-brand-700 shadow-sm">
          <Activity size={14} /> Platform foundation is being prepared
        </div>
        <h1 className="text-4xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-5xl">
          A clearer way to
          <span className="block bg-gradient-to-r from-brand-600 to-violet-500 bg-clip-text text-transparent">work together.</span>
        </h1>
        <p className="mt-5 max-w-xl text-base leading-7 text-slate-600">
          One trusted workspace for projects, agreements, communication and protected payments.
          This initial screen verifies that React can communicate with the API and database.
        </p>
        <div className="mt-8 flex flex-wrap gap-3 text-sm font-medium text-slate-600">
          {["Client workspace", "Freelancer workspace", "Payment infrastructure"].map((item) => (
            <span key={item} className="rounded-full bg-white/80 px-4 py-2 shadow-sm ring-1 ring-slate-200">{item}</span>
          ))}
        </div>
      </div>

      <div className="rounded-[2rem] border border-white/80 bg-white/75 p-6 shadow-soft backdrop-blur-xl sm:p-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-500">Development environment</p>
            <h2 className="mt-1 text-xl font-bold text-slate-900">Connection status</h2>
          </div>
          <div className="rounded-2xl bg-brand-50 p-3 text-brand-600"><Activity size={21} /></div>
        </div>
        <div className="mt-7 space-y-3">
          <StatusRow label="React frontend" detail="Vite development server" status="ok" />
          <StatusRow label="FastAPI backend" detail="GET /api/health" status={loading ? "loading" : health?.service === "api" ? "ok" : "error"} />
          <StatusRow label="PostgreSQL database" detail="SQLAlchemy · SELECT 1" status={loading ? "loading" : connected ? "ok" : "error"} />
        </div>
        {error && <div role="alert" className="mt-5 rounded-2xl border border-rose-100 bg-rose-50 p-4 text-sm leading-6 text-rose-700">{error}</div>}
        {connected && <div role="status" className="mt-5 rounded-2xl border border-emerald-100 bg-emerald-50 p-4 text-sm font-medium text-emerald-800">{health.message}</div>}
        <button type="button" onClick={checkConnection} disabled={loading}
          className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-600 to-violet-600 px-5 py-3.5 text-sm font-bold text-white shadow-lg shadow-brand-500/20 transition hover:-translate-y-0.5 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-70">
          {loading ? <LoaderCircle className="animate-spin" size={17} /> : <RefreshCw size={16} />}
          {loading ? "Checking services..." : "Check connection"}
        </button>
        <p className="mt-4 text-center text-xs text-slate-400">No dashboards or payment operations are enabled in Phase 1.</p>
      </div>
    </section>
  );
}

function StatusRow({ label, detail, status }) {
  const Icon = status === "loading" ? LoaderCircle : status === "ok" ? CheckCircle2 : CircleAlert;
  const iconClass = status === "ok" ? "text-emerald-500" : status === "error" ? "text-rose-500" : "text-brand-500";
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-100 bg-white/80 px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-slate-50 p-2 text-slate-500">
          {label.includes("PostgreSQL") ? <Database size={17} /> : <Server size={17} />}
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-800">{label}</p>
          <p className="mt-0.5 text-xs text-slate-400">{detail}</p>
        </div>
      </div>
      <Icon size={18} className={`${iconClass} ${status === "loading" ? "animate-spin" : ""}`} />
    </div>
  );
}
