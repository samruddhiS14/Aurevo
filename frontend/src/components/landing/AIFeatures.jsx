import { Sparkles, FileText, MessageSquareWarning, Scale } from "lucide-react";

const items = [
  [FileText, "Scope generation", "Turn project descriptions into structured scopes."],
  [Sparkles, "Milestone recommendations", "Suggest logical stages and deliverables."],
  [MessageSquareWarning, "Communication protection", "Identify suspicious off-platform transaction requests."],
  [Scale, "Dispute assistance", "Organize project records and evidence for review."],
];

export default function AIFeatures() {
  return (
    <section id="ai" className="rounded-[2rem] bg-[#F0EBFF] px-6 py-20 sm:px-12">
      <div className="mx-auto max-w-2xl text-center">
        <p className="font-bold text-[#7653D6]">INTELLIGENCE BUILT IN</p>
        <h2 className="mt-3 text-4xl font-extrabold text-[#242036]">
          AI that supports better decisions.
        </h2>
      </div>

      <div className="mt-12 grid gap-6 sm:grid-cols-2">
        {items.map(([Icon, title, description]) => (
          <div key={title} className="rounded-2xl bg-white p-6">
            <Icon className="text-[#7653D6]" size={27} />
            <h3 className="mt-4 font-bold text-[#242036]">{title}</h3>
            <p className="mt-2 text-sm leading-7 text-[#858096]">{description}</p>
          </div>
        ))}
      </div>
    </section>
  );
}