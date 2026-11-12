import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

const button = "rounded-xl bg-violet-700 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-800 disabled:opacity-50";

export default function ProjectsPage() {
  const { user } = useAuth();
  const client = user?.role === "CLIENT";
  const [projects, setProjects] = useState([]);
  const [proposal, setProposal] = useState({});
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(client ? "/api/v1/projects/mine" : "/api/v1/projects/");
      setProjects(data);
      setError("");
    } catch (e) {
      setError(e.response?.data?.detail || "Projects could not be loaded.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [client]);

  const updateProposal = (projectId, field, value) => {
    setProposal((current) => ({
      ...current,
      [projectId]: { proposal_text: "", proposed_amount: "", estimated_completion_days: "", relevant_experience: "", ...current[projectId], [field]: value },
    }));
  };

  const apply = async (project) => {
    const form = proposal[project.id] || {};
    if ((form.proposal_text || "").trim().length < 30 || (form.relevant_experience || "").trim().length < 20 || Number(form.proposed_amount) <= 0 || Number(form.estimated_completion_days) <= 0) {
      setError("Complete all proposal fields. Proposal must be 30+ characters and experience 20+ characters.");
      return;
    }
    try {
      await api.post(`/api/v1/projects/${project.id}/applications`, {
        proposal_text: form.proposal_text.trim(),
        proposed_amount: Number(form.proposed_amount),
        estimated_completion_days: Number(form.estimated_completion_days),
        relevant_experience: form.relevant_experience.trim(),
      });
      setStatus("Application submitted successfully.");
      setError("");
      setProjects((current) => current.filter((item) => item.id !== project.id));
    } catch (e) {
      setError(e.response?.data?.detail || "Application failed.");
    }
  };

  return (
    <main className="min-h-screen bg-[#f8f7ff] px-4 py-8 sm:px-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><Link to={client ? "/client/dashboard" : "/freelancer/dashboard"} className="text-sm font-semibold text-violet-700">← Dashboard</Link><h1 className="mt-2 text-3xl font-bold text-slate-900">{client ? "Your projects" : "Discover projects"}</h1><p className="text-sm text-slate-500">Live project records from Aurevo.</p></div>
          {client && <Link to="/client/projects/create" className={button}>Create project</Link>}
        </div>
        {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        {status && <p className="rounded-xl bg-green-50 p-3 text-sm text-green-700">{status}</p>}
        {loading ? <p className="rounded-2xl bg-white p-8 text-sm text-slate-500">Loading projects…</p> : (
          <div className="grid gap-4 md:grid-cols-2">
            {projects.map((project) => (
              <article key={project.id} className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-3"><h2 className="font-bold text-slate-900">{project.title}</h2><span className="rounded-full bg-violet-50 px-3 py-1 text-xs font-semibold capitalize text-violet-700">{project.status}</span></div>
                <p className="mt-2 line-clamp-3 text-sm text-slate-600">{project.description}</p>
                <div className="mt-3 text-xs text-slate-500">Budget: {project.currency} {project.budget ?? "Not specified"} · {project.category || "General"}</div>
                {client ? <div className="mt-4 flex flex-wrap gap-2"><Link className={button} to={`/client/projects/${project.id}/applications`}>View applications</Link>{project.freelancer_id && <Link className="rounded-xl border border-violet-200 px-4 py-2 text-sm font-semibold text-violet-700" to={`/client/projects/${project.id}/workspace`}>Open workspace</Link>}</div> : (
                  <div className="mt-4 space-y-2">
                    <label className="block text-xs font-semibold text-slate-600">Proposal<textarea rows={3} value={proposal[project.id]?.proposal_text || ""} onChange={(e) => updateProposal(project.id, "proposal_text", e.target.value)} placeholder="Explain how you will deliver this project (30+ characters)." className="mt-1 w-full rounded-xl border border-slate-200 p-3 text-sm" /></label>
                    <div className="grid grid-cols-2 gap-2"><label className="text-xs font-semibold text-slate-600">Your price ({project.currency})<input type="number" min="0.01" step="0.01" value={proposal[project.id]?.proposed_amount || ""} onChange={(e) => updateProposal(project.id, "proposed_amount", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 p-2.5 text-sm" /></label><label className="text-xs font-semibold text-slate-600">Delivery days<input type="number" min="1" step="1" value={proposal[project.id]?.estimated_completion_days || ""} onChange={(e) => updateProposal(project.id, "estimated_completion_days", e.target.value)} className="mt-1 w-full rounded-xl border border-slate-200 p-2.5 text-sm" /></label></div>
                    <label className="block text-xs font-semibold text-slate-600">Relevant experience<textarea rows={2} value={proposal[project.id]?.relevant_experience || ""} onChange={(e) => updateProposal(project.id, "relevant_experience", e.target.value)} placeholder="Describe relevant experience (20+ characters)." className="mt-1 w-full rounded-xl border border-slate-200 p-3 text-sm" /></label>
                    <button className={button} onClick={() => apply(project)}>Apply to project</button>
                  </div>
                )}
              </article>
            ))}
            {projects.length === 0 && <p className="rounded-2xl bg-white p-8 text-sm text-slate-500">{client ? "You have not created any projects yet." : "No open projects found."}</p>}
          </div>
        )}
      </div>
    </main>
  );
}
