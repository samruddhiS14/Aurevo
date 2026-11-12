import { Outlet } from "react-router-dom";
import { Sparkles } from "lucide-react";

export default function AppLayout() {
  return (
    <div className="page-glow min-h-screen">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-5 py-6 sm:px-8">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-violet-700 text-white shadow-soft">
            <Sparkles size={19} />
          </div>
          <div>
            <p className="text-sm font-extrabold tracking-tight text-slate-900">Aurevo</p>
            <p className="text-[11px] font-medium text-slate-500">AI-powered freelance collaboration & FinTech.</p>
          </div>
        </div>
        <span className="rounded-full border border-brand-100 bg-white/70 px-3 py-1.5 text-xs font-semibold text-brand-700 shadow-sm">
          Client + Freelancer Workspace
        </span>
      </header>
      <main className="mx-auto max-w-6xl px-5 pb-16 sm:px-8"><Outlet /></main>
    </div>
  );
}
