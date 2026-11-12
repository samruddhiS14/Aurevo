import {
  BrainCircuit,
  ShieldCheck,
  Milestone,
  MessagesSquare,
  Users,
  Scale,
} from "lucide-react";

const features = [
  {
    icon: BrainCircuit,
    title: "AI Project Planning",
    description: "Generate clear project scopes and structured deliverables.",
  },
  {
    icon: Milestone,
    title: "Smart Milestones",
    description: "Break complex projects into manageable stages.",
  },
  {
    icon: ShieldCheck,
    title: "Payment Management",
    description: "Manage single and milestone-based payment workflows.",
  },
  {
    icon: MessagesSquare,
    title: "Built-in Messaging",
    description: "Keep project communication within one workspace.",
  },
  {
    icon: Users,
    title: "Smarter Hiring",
    description: "Connect clients with freelancers through applications.",
  },
  {
    icon: Scale,
    title: "Dispute Assistance",
    description: "Use AI-assisted evidence organization for disagreements.",
  },
];

export default function Features() {
  return (
    <section id="features" className="py-24">
      <div className="mx-auto mb-12 max-w-2xl text-center">
        <p className="font-bold text-[#7653D6]">PLATFORM FEATURES</p>

        <h2 className="mt-3 text-4xl font-extrabold text-[#242036]">
          Everything in one workspace.
        </h2>

        <p className="mt-4 text-[#858096]">
          From the first project discussion to the final payment.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map(({ icon: Icon, title, description }) => (
          <div key={title} className="rounded-2xl border border-purple-100
            bg-white p-7 shadow-sm transition hover:-translate-y-1
            hover:shadow-lg">
            <div className="mb-5 inline-flex rounded-xl bg-[#EAE3FF] p-3">
              <Icon className="text-[#7653D6]" size={25} />
            </div>

            <h3 className="text-lg font-bold text-[#242036]">
              {title}
            </h3>

            <p className="mt-3 text-sm leading-7 text-[#858096]">
              {description}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}