import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import api from "../../services/api";

const statLabels = { users: "Total users", clients: "Clients", freelancers: "Freelancers", projects: "Projects", open_disputes: "Open disputes", payments: "PayPal payments", flagged_messages: "Flagged messages", unprocessed_webhooks: "Webhook exceptions" };

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [disputes, setDisputes] = useState([]);
  const [logs, setLogs] = useState([]);
  const [payments, setPayments] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [activity, setActivity] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    setError("");
    try {
      const [s, u, p, d, l, pay, wh, act] = await Promise.all([api.get("/api/v1/admin/dashboard"), api.get("/api/v1/admin/users?page_size=8"), api.get("/api/v1/admin/projects?page_size=8"), api.get("/api/v1/admin/disputes?page_size=8"), api.get("/api/v1/admin/detection-logs?page_size=8"), api.get("/api/v1/admin/payments?page_size=8"), api.get("/api/v1/admin/webhooks?page_size=8"), api.get("/api/v1/admin/activity?page_size=8")]);
      setStats(s.data); setUsers(u.data.items); setProjects(p.data.items); setDisputes(d.data.items); setLogs(l.data.items); setPayments(pay.data.items); setWebhooks(wh.data.items); setActivity(act.data.items);
    } catch (e) { setError(e.response?.data?.detail || "Unable to load admin data. Check your admin role and backend connection."); }
  }

  useEffect(() => { load(); }, []);

  async function toggleUser(u) {
    setBusyId(u.id);
    try { await api.patch(`/api/v1/admin/users/${u.id}/active?active=${!u.is_active}`); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Could not update this account."); }
    finally { setBusyId(null); }
  }

  function signOut() { logout(); navigate("/admin/login", { replace: true }); }

  return <main className="min-h-screen bg-[#F7F5FC] px-4 py-6 sm:px-8">
    <div className="mx-auto max-w-7xl space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-violet-100">
        <div><p className="text-xs font-bold uppercase tracking-[.2em] text-violet-600">Aurevo · Administration</p><h1 className="mt-1 text-2xl font-extrabold text-slate-900">Platform overview</h1><p className="mt-1 text-sm text-slate-500">Signed in as {user?.full_name || user?.email}</p></div>
        <div className="flex gap-2"><button onClick={load} className="rounded-xl border border-violet-200 px-4 py-2 text-sm font-semibold text-violet-700">Refresh</button><button onClick={signOut} className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Sign out</button></div>
      </header>
      {error && <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(statLabels).map(([key,label]) => <article key={key} className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-extrabold text-slate-900">{stats ? stats[key] : "—"}</p></article>)}
      </section>
      <section className="grid gap-5 xl:grid-cols-2">
        <Panel title="User management"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="text-slate-500"><th className="py-2">User</th><th>Role</th><th>Status</th><th></th></tr></thead><tbody>{users.map(u => <tr key={u.id} className="border-t border-slate-100"><td className="py-3"><div className="font-semibold">{u.full_name}</div><div className="text-xs text-slate-500">{u.email}</div></td><td>{u.role}</td><td>{u.is_active ? "Active" : "Inactive"}</td><td><button disabled={u.role === "ADMIN" || busyId === u.id} onClick={() => toggleUser(u)} className="text-xs font-bold text-violet-700 disabled:opacity-40">{u.is_active ? "Deactivate" : "Activate"}</button></td></tr>)}</tbody></table></div></Panel>
        <Panel title="Recent projects"><Rows rows={projects} render={p => <><b>#{p.id} · {p.title}</b><span className="text-slate-500">{p.status} · {p.currency} {p.budget ?? "—"}</span></>} /></Panel>
        <Panel title="Dispute monitoring"><Rows rows={disputes} render={d => <><b>Dispute #{d.id} · Project #{d.project_id}</b><span className="text-slate-500">{d.status} · {d.reason}</span></>} empty="No disputes recorded." /></Panel>
        <Panel title="AI off-platform detection logs"><Rows rows={logs} render={l => <><b>Message #{l.id} · Project #{l.project_id}</b><span className="text-slate-500">{l.warning_reasons || "Flagged message"}</span></>} empty="No flagged messages recorded." /></Panel>
        <Panel title="PayPal payment monitoring"><Rows rows={payments} render={p => <><b>Payment #{p.id} · Project #{p.project_id}</b><span className="text-slate-500">{p.currency} {p.amount} · {p.status}{p.paypal_amount && p.paypal_currency ? ` · PayPal ${p.paypal_currency} ${p.paypal_amount}` : ""}</span>{p.failure_reason && <span className="text-amber-700">Reconciliation: {p.failure_reason}</span>}</>} empty="No payment records found." /></Panel>
        <Panel title="Webhook events"><Rows rows={webhooks} render={w => <><b>{w.event_type}</b><span className="text-slate-500">{w.processed} · {w.event_id}</span></>} empty="No webhook events found." /></Panel>
        <Panel title="Platform activity / audit trail"><Rows rows={activity} render={a => <><b>{a.title} · Project #{a.project_id}</b><span className="text-slate-500">{a.description || "Activity recorded"}</span></>} empty="No activity records found." /></Panel>
      </section>
      <p className="text-xs text-slate-500">Administrative monitoring only. Payment capture, dispute outcomes and AI decisions are not controlled from this dashboard.</p>
    </div>
  </main>;
}

function Panel({ title, children }) { return <section className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm"><h2 className="mb-3 font-bold text-slate-900">{title}</h2>{children}</section>; }
function Rows({ rows, render, empty = "No records found." }) { return rows.length ? <ul className="divide-y divide-slate-100">{rows.map(row => <li key={row.id} className="flex flex-col gap-1 py-3 text-sm">{render(row)}</li>)}</ul> : <p className="py-5 text-sm text-slate-500">{empty}</p>; }
