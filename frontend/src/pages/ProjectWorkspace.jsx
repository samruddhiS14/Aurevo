import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

const card = "rounded-2xl border border-violet-100 bg-white p-5 shadow-sm";
const button = "rounded-xl bg-violet-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-800 disabled:opacity-50";

export default function ProjectWorkspace() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [messages, setMessages] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [scopeVersions, setScopeVersions] = useState([]);
  const [agreementVersions, setAgreementVersions] = useState([]);
  const [agreementDraft, setAgreementDraft] = useState("");
  const [agreementDraftVersionId, setAgreementDraftVersionId] = useState(null);
  const [changeSummary, setChangeSummary] = useState("");
  const [disputes, setDisputes] = useState([]);
  const [evidenceFile, setEvidenceFile] = useState(null);
  const [content, setContent] = useState("");
  const [file, setFile] = useState(null);
  const [disputeReason, setDisputeReason] = useState({});
  const [submissionNotes, setSubmissionNotes] = useState({});
  const [revisionNotes, setRevisionNotes] = useState({});
  const [progressValues, setProgressValues] = useState({});
  const [activeDispute, setActiveDispute] = useState(null);
  const [evidenceText, setEvidenceText] = useState("");
  const [copilotQuestion, setCopilotQuestion] = useState("");
  const [copilotAnswer, setCopilotAnswer] = useState("");
  const [aiReport, setAiReport] = useState(null);
  const [resolutionSummary, setResolutionSummary] = useState("");
  const [resolutionOutcome, setResolutionOutcome] = useState("submitted");
  const [reviewRating, setReviewRating] = useState("5");
  const [reviewComment, setReviewComment] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError("");
      const [p, m, ms, scopes, ds, agreements] = await Promise.all([
        api.get(`/api/v1/projects/${projectId}`),
        api.get(`/api/v1/projects/${projectId}/messages`),
        api.get(`/api/milestones/projects/${projectId}`),
        api.get(`/api/v1/ai/projects/${projectId}/scope`),
        api.get(`/api/v1/disputes/projects/${projectId}`),
        api.get(`/api/v1/agreements/projects/${projectId}/versions`),
      ]);
      setProject(p.data); setMessages(m.data); setMilestones(ms.data); setScopeVersions(scopes.data); setDisputes(ds.data);
      setAgreementVersions(agreements.data);
    } catch (e) { setError(e.response?.data?.detail || "Unable to load this project workspace."); }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const latest = agreementVersions[0];
    if (latest?.agreement_data && latest.id !== agreementDraftVersionId) {
      setAgreementDraft(JSON.stringify(latest.agreement_data, null, 2));
      setAgreementDraftVersionId(latest.id);
    }
  }, [agreementVersions, agreementDraftVersionId]);

  const send = async (event) => {
    event.preventDefault();
    if (!content.trim() && !file) return;
    setBusy(true); setError("");
    try {
      if (file) {
        const form = new FormData(); form.append("file", file); form.append("content", content.trim() || "Shared a file.");
        await api.post(`/api/v1/projects/${projectId}/messages/attachment`, form, { headers: { "Content-Type": "multipart/form-data" } });
      } else {
        await api.post(`/api/v1/projects/${projectId}/messages`, { content });
      }
      setContent(""); setFile(null); await load();
    } catch (e) { setError(e.response?.data?.detail || "Message could not be sent."); }
    finally { setBusy(false); }
  };


  const uploadDeliverable = async (milestone, selectedFile) => {
    if (!selectedFile) return;
    setBusy(true); setError("");
    try { if (milestone.status === "not_started") await api.patch(`/api/milestones/${milestone.id}/progress`, { progress_percentage: 1 }); const form = new FormData(); form.append("file", selectedFile); await api.post(`/api/milestones/${milestone.id}/upload`, form, { headers: { "Content-Type": "multipart/form-data" } }); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Deliverable upload failed."); }
    finally { setBusy(false); }
  };

  const updateProgress = async (milestoneId, value) => {
    try { await api.patch(`/api/milestones/${milestoneId}/progress`, { progress_percentage: Number(value) }); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Progress update failed."); }
  };

  const submitMilestone = async (milestone) => {
    const fileIds = (milestone.submission_url || "").split(",").filter(Boolean);
    const notes = submissionNotes[milestone.id] || milestone.submission_notes || "";
    if (!fileIds.length || notes.trim().length < 10) { setError("Upload at least one deliverable and add submission notes (10+ characters)."); return; }
    setBusy(true); setError("");
    try { await api.post(`/api/milestones/${milestone.id}/submit`, { submission_url: fileIds.join(","), submission_notes: notes }); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Milestone submission failed."); }
    finally { setBusy(false); }
  };

  const startMilestoneReview = async (milestoneId) => {
    try { await api.post(`/api/milestones/${milestoneId}/start-review`); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Could not start milestone review."); }
  };

  const reviewMilestone = async (milestoneId, action) => {
    const explanation = revisionNotes[milestoneId] || "";
    if (action === "request_revision" && explanation.trim().length < 10) { setError("Explain the requested revision (10+ characters)."); return; }
    setBusy(true); setError("");
    try { await api.post(`/api/milestones/${milestoneId}/review`, { action, explanation: action === "request_revision" ? explanation : null }); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Milestone review failed."); }
    finally { setBusy(false); }
  };

  const downloadDeliverable = async (milestoneId, fileId) => {
    try { const response = await api.get(`/api/milestones/files/${encodeURIComponent(fileId)}`, { responseType: "blob" }); const url = URL.createObjectURL(response.data); const anchor = document.createElement("a"); anchor.href = url; anchor.download = fileId; anchor.click(); URL.revokeObjectURL(url); }
    catch { setError("Deliverable download failed."); }
  };

  const openDispute = async (milestoneId) => {
    const reason = disputeReason[milestoneId] || "";
    setBusy(true); setError("");
    try {
      const { data } = await api.post(`/api/v1/disputes/milestones/${milestoneId}`, { reason });
      setActiveDispute(data.id); await load();
    } catch (e) { setError(e.response?.data?.detail || "Could not open dispute."); }
    finally { setBusy(false); }
  };

  const addEvidence = async (event) => {
    event.preventDefault(); if (!activeDispute || (!evidenceText.trim() && !evidenceFile)) return;
    try {
      if (evidenceFile) {
        const form = new FormData(); form.append("file", evidenceFile); form.append("description", evidenceText.trim() || "Supporting evidence attachment");
        await api.post(`/api/v1/disputes/${activeDispute}/evidence/file`, form, { headers: { "Content-Type": "multipart/form-data" } });
      } else {
        await api.post(`/api/v1/disputes/${activeDispute}/evidence`, { description: evidenceText });
      }
      setEvidenceText(""); setEvidenceFile(null);
      const { data } = await api.get(`/api/v1/disputes/${activeDispute}`); setAiReport(data); await load();
    } catch (e) { setError(e.response?.data?.detail || "Evidence could not be added."); }
  };

  const viewDispute = async (id) => {
    setActiveDispute(id);
    try { const { data } = await api.get(`/api/v1/disputes/${id}`); setAiReport(data); }
    catch (e) { setError(e.response?.data?.detail || "Dispute could not be loaded."); }
  };


  const proposeResolution = async (event) => {
    event.preventDefault(); if (!activeDispute || resolutionSummary.trim().length < 20) return;
    try { await api.post(`/api/v1/disputes/${activeDispute}/propose-resolution`, { summary: resolutionSummary, milestone_outcome: resolutionOutcome }); const { data } = await api.get(`/api/v1/disputes/${activeDispute}`); setAiReport(data); setResolutionSummary(""); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Resolution proposal failed."); }
  };
  const respondResolution = async (action) => {
    if (!activeDispute) return;
    try { await api.post(`/api/v1/disputes/${activeDispute}/${action}-resolution`); const { data } = await api.get(`/api/v1/disputes/${activeDispute}`); setAiReport(data); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Could not update resolution."); }
  };

  const runReport = async () => {
    if (!activeDispute) return;
    setBusy(true);
    try { const { data } = await api.post(`/api/v1/disputes/${activeDispute}/ai-report`); setAiReport(data); }
    catch (e) { setError(e.response?.data?.detail || "AI report is unavailable."); }
    finally { setBusy(false); }
  };



  const submitProjectReview = async (event) => {
    event.preventDefault();
    try { await api.post(`/api/v1/projects/${projectId}/reviews`, { rating: Number(reviewRating), comment: reviewComment }); setReviewComment(""); setError(""); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Review could not be submitted."); }
  };

  const generateScope = async () => {
    setBusy(true); setError("");
    try { await api.post(`/api/v1/ai/projects/${projectId}/scope`, { additional_instructions: "Create a clear, testable scope based only on the project brief." }); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Scope generation failed. Check Gemini configuration and project budget."); }
    finally { setBusy(false); }
  };


  const generateAgreement = async () => {
    setBusy(true); setError("");
    try { await api.post(`/api/v1/agreements/projects/${projectId}/generate`, { change_summary: "Initial agreement generated from the approved AI scope." }); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Agreement generation failed. Approve the AI scope and assign a freelancer first."); }
    finally { setBusy(false); }
  };

  const approveAgreement = async (versionId) => {
    setBusy(true); setError("");
    try { await api.post(`/api/v1/agreements/versions/${versionId}/approve`, { confirm: true }); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Agreement approval failed."); }
    finally { setBusy(false); }
  };


  const proposeAgreementChanges = async (event) => {
    event.preventDefault();
    const latest = agreementVersions[0];
    if (!latest?.agreement_id || changeSummary.trim().length < 5) {
      setError("Provide a clear change summary of at least 5 characters.");
      return;
    }
    let agreementData;
    try { agreementData = JSON.parse(agreementDraft); }
    catch { setError("Agreement details must be valid JSON. Review the edited agreement before submitting."); return; }
    setBusy(true); setError("");
    try {
      await api.post(`/api/v1/agreements/${latest.agreement_id}/versions`, {
        agreement_data: agreementData,
        change_summary: changeSummary.trim(),
      });
      setChangeSummary("");
      await load();
    } catch (e) {
      setError(e.response?.data?.detail || "Agreement revision could not be proposed.");
    } finally { setBusy(false); }
  };

  const approveScope = async (scopeId) => {
    setBusy(true);
    try { await api.post(`/api/v1/ai/scope/${scopeId}/approve`); await load(); }
    catch (e) { setError(e.response?.data?.detail || "Scope approval failed."); }
    finally { setBusy(false); }
  };

  const askCopilot = async (event) => {
    event.preventDefault(); if (!copilotQuestion.trim()) return;
    setBusy(true);
    try { const { data } = await api.post(`/api/v1/ai/projects/${projectId}/copilot`, { question: copilotQuestion }); setCopilotAnswer(data.answer); }
    catch (e) { setError(e.response?.data?.detail || "Copilot is unavailable. Check the Gemini configuration."); }
    finally { setBusy(false); }
  };

  const downloadAttachment = async (message) => {
    try {
      const response = await api.get(`/api/v1/projects/${projectId}/messages/${message.id}/attachment`, { responseType: "blob" });
      const url = URL.createObjectURL(response.data); const anchor = document.createElement("a"); anchor.href = url; anchor.download = message.attachment_name || "attachment"; anchor.click(); URL.revokeObjectURL(url);
    } catch { setError("Attachment download failed."); }
  };

  return (
    <main className="min-h-screen bg-[#f8f7ff] px-4 py-7 sm:px-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><Link to={user?.role === "CLIENT" ? "/client/dashboard" : "/freelancer/dashboard"} className="text-sm font-semibold text-violet-700">← Dashboard</Link><h1 className="mt-2 text-2xl font-bold text-slate-900">{project?.title || "Project workspace"}</h1><p className="text-sm text-slate-500">Messages, milestone reviews, evidence and AI assistance</p></div>
          <button className={button} onClick={load}>Refresh workspace</button>
        </div>
        {error && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        <div className="grid gap-6 lg:grid-cols-[1.15fr_.85fr]">
          <section className={`${card} flex min-h-[620px] flex-col`}>
            <div className="mb-4 flex items-center justify-between"><h2 className="font-bold text-slate-900">Project chat</h2><span className="text-xs text-slate-500">Private to project participants</span></div>
            <div className="flex-1 space-y-3 overflow-y-auto rounded-xl bg-slate-50 p-3">
              {messages.length === 0 && <p className="p-5 text-center text-sm text-slate-500">No messages yet. Start the project conversation.</p>}
              {messages.map((m) => <div key={m.id} className={`max-w-[90%] rounded-2xl p-3 text-sm ${m.is_mine ? "ml-auto bg-violet-100 text-violet-950" : "bg-white text-slate-800 shadow-sm"}`}>
                <div className="mb-1 flex justify-between gap-4 text-[11px] text-slate-500"><span>{m.is_mine ? "You" : "Project participant"}</span><span>{new Date(m.created_at).toLocaleString()}</span></div>
                <p className="whitespace-pre-wrap">{m.content}</p>
                {m.has_attachment && <button className="mt-2 underline" onClick={() => downloadAttachment(m)}>Download {m.attachment_name}</button>}
                {m.policy_warning && <div className="mt-3 rounded-xl border border-amber-300 bg-amber-50 p-3 text-amber-950"><p className="font-bold">{m.policy_warning.title}</p><p className="mt-1 text-xs">{m.policy_warning.message}</p><p className="mt-1 text-xs">{m.policy_warning.paypal_notice}</p></div>}
              </div>)}
            </div>
            <form onSubmit={send} className="mt-4 space-y-3">
              <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={3} placeholder="Write a project message..." className="w-full rounded-xl border border-slate-200 p-3 text-sm outline-none focus:border-violet-400" />
              <div className="flex flex-wrap items-center justify-between gap-3"><input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="max-w-full text-xs text-slate-500" /><button className={button} disabled={busy || (!content.trim() && !file)}>Send message</button></div>
            </form>
          </section>
          <div className="space-y-6">
            <section className={card}><h2 className="font-bold text-slate-900">Milestones & disputes</h2><div className="mt-4 space-y-4">
              {milestones.map((m) => <div key={m.id} className="rounded-xl border border-slate-100 p-3"><div className="flex items-start justify-between gap-3"><div><p className="font-semibold text-slate-800">{m.title}</p><p className="mt-1 text-xs text-slate-600">{m.description}</p><p className="text-xs capitalize text-violet-700">{m.status} · {m.currency} {m.amount}</p>{m.deliverables?.length > 0 && <p className="text-xs text-slate-500">Deliverables: {m.deliverables.join(", ")}</p>}{m.submission_notes && <p className="mt-2 rounded-lg bg-violet-50 p-2 text-xs text-slate-700">Submission notes: {m.submission_notes}</p>}{m.review_deadline && <p className="mt-1 text-xs text-slate-500">Review deadline: {new Date(m.review_deadline).toLocaleString()}</p>}{m.revision_explanation && <p className="mt-2 rounded-lg bg-amber-50 p-2 text-xs text-amber-900">Revision requested: {m.revision_explanation}</p>}</div></div>
                {(m.submission_url || "").split(",").filter(Boolean).map(fileId => <button key={fileId} onClick={() => downloadDeliverable(m.id, fileId)} className="mr-2 mt-2 text-xs text-violet-700 underline">Download {fileId.slice(0, 12)}</button>)}
                {user?.role === "FREELANCER" && ["not_started","in_progress","revision_requested"].includes(m.status) && <div className="mt-3 space-y-2 rounded-xl bg-slate-50 p-3"><label className="block text-xs font-semibold text-slate-600">Progress: {progressValues[m.id] ?? m.progress_percentage}%<input type="range" min="0" max="99" value={progressValues[m.id] ?? m.progress_percentage} onChange={e => setProgressValues(v => ({...v,[m.id]:e.target.value}))} onMouseUp={e => updateProgress(m.id,e.target.value)} onTouchEnd={e => updateProgress(m.id,e.currentTarget.value)} className="mt-2 w-full" /></label><label className="block text-xs font-semibold text-slate-600">Upload deliverable<input type="file" onChange={e => uploadDeliverable(m,e.target.files?.[0])} className="mt-1 block text-xs" /></label><textarea value={submissionNotes[m.id] ?? m.submission_notes ?? ""} onChange={e => setSubmissionNotes(v => ({...v,[m.id]:e.target.value}))} rows={2} placeholder="Submission notes (10+ characters)" className="w-full rounded-lg border border-slate-200 p-2 text-xs"/><button disabled={busy || !(m.submission_url || "").trim() || (submissionNotes[m.id] ?? m.submission_notes ?? "").trim().length < 10} onClick={() => submitMilestone(m)} className={button}>Submit milestone for review</button></div>}
                {user?.role === "CLIENT" && ["submitted","under_review"].includes(m.status) && <div className="mt-3 space-y-2 rounded-xl bg-slate-50 p-3">{m.status === "submitted" && <button onClick={() => startMilestoneReview(m.id)} className="rounded-lg border border-violet-200 px-3 py-2 text-xs font-semibold text-violet-700">Start review</button>}<textarea value={revisionNotes[m.id] || ""} onChange={e => setRevisionNotes(v => ({...v,[m.id]:e.target.value}))} rows={2} placeholder="Explain requested changes if revisions are needed..." className="w-full rounded-lg border border-slate-200 p-2 text-xs"/><div className="flex flex-wrap gap-2"><button disabled={busy} onClick={() => reviewMilestone(m.id,"approve")} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white">Approve work</button><button disabled={busy || (revisionNotes[m.id] || "").trim().length < 10} onClick={() => reviewMilestone(m.id,"request_revision")} className="rounded-lg border border-amber-300 px-3 py-2 text-xs font-semibold text-amber-800">Request revision</button></div></div>}
                {!['paid','disputed'].includes(m.status) && <div className="mt-3 space-y-2"><textarea value={disputeReason[m.id] || ""} onChange={(e) => setDisputeReason((v) => ({...v, [m.id]: e.target.value}))} rows={2} placeholder="Explain a dispute (minimum 20 characters)" className="w-full rounded-lg border border-slate-200 p-2 text-xs" /><button disabled={busy || (disputeReason[m.id] || "").trim().length < 20} className="rounded-lg border border-amber-300 px-3 py-2 text-xs font-semibold text-amber-800" onClick={() => openDispute(m.id)}>Open evidence-based dispute</button></div>}
              </div>)}
              {!milestones.length && <p className="text-sm text-slate-500">No milestones have been created for this project yet.</p>}
            </div></section>
            <section className={card}><h2 className="font-bold text-slate-900">Dispute evidence</h2><p className="mt-1 text-xs text-slate-500">Enter the dispute ID returned when you open a dispute to add evidence.</p><div className="mt-3 space-y-2">{disputes.map(d => <button key={d.id} onClick={() => viewDispute(d.id)} className="mr-2 rounded-lg border border-amber-200 px-3 py-2 text-xs font-semibold text-amber-800">Dispute #{d.id} · {d.status}</button>)}</div><form onSubmit={addEvidence} className="mt-3 space-y-2"><input type="number" min="1" value={activeDispute || ""} onChange={(e) => setActiveDispute(Number(e.target.value) || null)} placeholder="Dispute ID" className="w-full rounded-lg border border-slate-200 p-2 text-sm" /><textarea value={evidenceText} onChange={(e) => setEvidenceText(e.target.value)} rows={2} placeholder="Describe supporting evidence..." className="w-full rounded-lg border border-slate-200 p-2 text-sm" /><input type="file" onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)} className="text-xs text-slate-500" /><button className={button} disabled={!activeDispute || (!evidenceText.trim() && !evidenceFile)}>Add evidence</button></form><button onClick={runReport} disabled={!activeDispute || busy} className="mt-3 rounded-xl border border-violet-200 px-4 py-2 text-sm font-semibold text-violet-700">Generate neutral AI evidence report</button>{aiReport?.resolution_summary && <div className="mt-3 rounded-xl bg-amber-50 p-3 text-sm"><p className="font-semibold">Pending mutual resolution</p><p className="mt-1">{aiReport.resolution_summary}</p><p className="mt-1 text-xs">Outcome: {aiReport.resolution_outcome} · Client accepted: {String(aiReport.client_accepted)} · Freelancer accepted: {String(aiReport.freelancer_accepted)}</p><div className="mt-2 flex gap-2"><button onClick={() => respondResolution("accept")} className="rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white">Accept proposal</button><button onClick={() => respondResolution("reject")} className="rounded-lg border border-amber-300 px-3 py-2 text-xs font-semibold text-amber-800">Reject proposal</button></div></div>}<form onSubmit={proposeResolution} className="mt-3 space-y-2"><textarea value={resolutionSummary} onChange={(e) => setResolutionSummary(e.target.value)} rows={2} placeholder="Propose a mutually agreed resolution (20+ characters)..." className="w-full rounded-lg border border-slate-200 p-2 text-sm"/><select value={resolutionOutcome} onChange={(e) => setResolutionOutcome(e.target.value)} className="w-full rounded-lg border border-slate-200 p-2 text-sm"><option value="submitted">Return milestone to submitted for client review</option><option value="revision_requested">Return milestone to revision requested</option></select><button disabled={!activeDispute || resolutionSummary.trim().length < 20} className="rounded-lg border border-violet-200 px-3 py-2 text-xs font-semibold text-violet-700">Propose mutual resolution</button></form>{aiReport && <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-slate-50 p-3 text-xs text-slate-700">{JSON.stringify(aiReport, null, 2)}</pre>}</section>
            {milestones.length > 0 && milestones.every(m => m.status === "paid") && <section className={card}><h2 className="font-bold text-slate-900">Review your project partner</h2><form onSubmit={submitProjectReview} className="mt-3 space-y-2"><select value={reviewRating} onChange={e => setReviewRating(e.target.value)} className="w-full rounded-lg border border-slate-200 p-2 text-sm"><option value="5">5 — Excellent</option><option value="4">4 — Very good</option><option value="3">3 — Good</option><option value="2">2 — Needs improvement</option><option value="1">1 — Poor</option></select><textarea value={reviewComment} onChange={e => setReviewComment(e.target.value)} rows={3} placeholder="Write a review (optional)..." className="w-full rounded-lg border border-slate-200 p-2 text-sm"/><button className={button}>Submit project review</button></form></section>}
            <section className={card}><div className="flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-bold text-slate-900">AI scope & milestone plan</h2><p className="mt-1 text-xs text-slate-500">Generated drafts require client review and approval.</p></div>{user?.role === "CLIENT" && <button onClick={generateScope} disabled={busy} className={button}>Generate scope draft</button>}</div><div className="mt-3 space-y-3">{scopeVersions.map((scope) => <div key={scope.id} className="rounded-xl border border-slate-100 p-3"><div className="flex items-center justify-between gap-2"><p className="font-semibold text-sm">Scope v{scope.version_number}</p><span className="text-xs capitalize text-violet-700">{scope.status}</span></div><p className="mt-2 text-xs text-slate-600">{(scope.scope_data?.project_objectives || []).slice(0,3).join(" · ")}</p>{!scope.is_approved && user?.role === "CLIENT" && <button onClick={() => approveScope(scope.id)} disabled={busy} className="mt-3 rounded-lg border border-violet-200 px-3 py-2 text-xs font-semibold text-violet-700">Approve this scope</button>}</div>)}{!scopeVersions.length && <p className="text-sm text-slate-500">No AI scope draft yet.</p>}</div><p className="mt-2 text-[11px] text-slate-500">The AI proposes scope only. Both parties must approve the agreement before milestones and payment actions are available.</p></section>
            <section className={card}>
              <div className="flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-bold text-slate-900">Project agreement</h2><p className="mt-1 text-xs text-slate-500">Both participants approve the same immutable version. Changes create a new version.</p></div>{user?.role === "CLIENT" && scopeVersions.some(s => s.is_approved) && agreementVersions.length === 0 && <button onClick={generateAgreement} disabled={busy} className={button}>Generate agreement</button>}</div>
              <div className="mt-3 space-y-3">
                {agreementVersions.map(v => <div key={v.id} className="rounded-xl border border-slate-100 p-3"><div className="flex items-center justify-between gap-2"><p className="font-semibold text-sm">Agreement v{v.version_number}</p><span className="text-xs capitalize text-violet-700">{v.status}</span></div><p className="mt-2 text-xs text-slate-600">Client: {v.client_approved ? "Approved" : "Pending"} · Freelancer: {v.freelancer_approved ? "Approved" : "Pending"}</p>{v.change_summary && <p className="mt-2 text-xs text-slate-600">Change summary: {v.change_summary}</p>}{v.agreement_data?.milestones?.length > 0 && <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-slate-600">{v.agreement_data.milestones.map((milestone, index) => <li key={`${v.id}-${index}`}>{milestone.title} — {milestone.currency} {milestone.amount}</li>)}</ul>}{v.status === "pending_approval" && ((user?.role === "CLIENT" && !v.client_approved) || (user?.role === "FREELANCER" && !v.freelancer_approved)) && <button onClick={() => approveAgreement(v.id)} disabled={busy} className="mt-3 rounded-lg border border-violet-200 px-3 py-2 text-xs font-semibold text-violet-700">Approve agreement version</button>}</div>)}
                {!agreementVersions.length && <p className="text-sm text-slate-500">Generate the agreement after the AI scope is approved.</p>}
              </div>
              {agreementVersions[0]?.status === "active" && <form onSubmit={proposeAgreementChanges} className="mt-4 space-y-2 border-t border-slate-100 pt-4"><h3 className="text-sm font-semibold text-slate-800">Propose changes</h3><p className="text-xs text-slate-500">Edit the agreement JSON below. The server validates milestone amounts, currency, and required fields before creating a new pending version.</p><textarea value={agreementDraft} onChange={e => setAgreementDraft(e.target.value)} rows={10} className="w-full rounded-xl border border-slate-200 p-3 font-mono text-xs" aria-label="Proposed agreement JSON"/><input value={changeSummary} onChange={e => setChangeSummary(e.target.value)} placeholder="Summarize the requested changes (5+ characters)" className="w-full rounded-xl border border-slate-200 p-3 text-sm"/><button disabled={busy || changeSummary.trim().length < 5} className={button}>Submit new agreement version</button></form>}
            </section>
            <section className={card}><h2 className="font-bold text-slate-900">Aurevo Copilot</h2><form onSubmit={askCopilot} className="mt-3 space-y-2"><textarea value={copilotQuestion} onChange={(e) => setCopilotQuestion(e.target.value)} rows={2} placeholder="Ask about the scope, milestone criteria or next steps..." className="w-full rounded-lg border border-slate-200 p-2 text-sm" /><button className={button} disabled={busy || copilotQuestion.trim().length < 3}>Ask Copilot</button></form>{copilotAnswer && <p className="mt-3 whitespace-pre-wrap rounded-xl bg-violet-50 p-3 text-sm text-slate-800">{copilotAnswer}</p>}<p className="mt-2 text-[11px] text-slate-500">AI guidance is advisory. It cannot approve work or authorize/capture payments.</p></section>
          </div>
        </div>
      </div>
    </main>
  );
}
