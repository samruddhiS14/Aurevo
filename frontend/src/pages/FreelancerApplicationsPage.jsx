import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
export default function FreelancerApplicationsPage() {
  const [applications, setApplications] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const load = async () => {
    setLoading(true);
    try { const { data } = await api.get("/api/v1/projects/applications/mine"); setApplications(data); setError(""); }
    catch (e) { setError(e.response?.data?.detail || "Applications could not be loaded."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const withdraw = async (id) => {
    try { await api.post(`/api/v1/projects/applications/${id}/withdraw`); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Application could not be withdrawn."); }
  };
  return <main className="min-h-screen bg-[#f8f7ff] px-4 py-8"><div className="mx-auto max-w-5xl space-y-5"><Link to="/freelancer/dashboard" className="text-sm font-semibold text-violet-700">← Dashboard</Link><h1 className="text-3xl font-bold text-slate-900">My applications</h1>{error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}{loading && <p className="rounded-2xl bg-white p-8 text-sm text-slate-500">Loading applications…</p>}{applications.map((application) => <article key={application.id} className="rounded-2xl border border-violet-100 bg-white p-5"><div className="flex flex-wrap justify-between gap-2"><p className="font-semibold text-slate-900">{application.project_title || `Project #${application.project_id}`}</p><span className="rounded-full bg-violet-50 px-3 py-1 text-xs capitalize text-violet-700">{application.status}</span></div><p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{application.proposal_text}</p><p className="mt-2 text-xs text-slate-500">Proposed: {application.currency || ""} {application.proposed_amount ?? "Not provided"} · {application.estimated_completion_days ?? "—"} days</p>{application.status === "accepted" && <Link to={`/freelancer/projects/${application.project_id}/workspace`} className="mt-3 inline-block rounded-xl bg-violet-700 px-4 py-2 text-sm font-semibold text-white">Open project workspace</Link>}{["pending", "shortlisted"].includes(application.status) && <button onClick={() => withdraw(application.id)} className="mt-3 ml-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700">Withdraw</button>}</article>)}{!loading && !applications.length && !error && <p className="rounded-2xl bg-white p-8 text-sm text-slate-500">You have not applied to any projects yet.</p>}</div></main>;
}
