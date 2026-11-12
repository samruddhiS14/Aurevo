import { Link } from "react-router-dom";
import {
  ArrowRight,
  ShieldCheck,
  Sparkles,
  CircleCheck,
} from "lucide-react";
import Button from "../ui/Button";
import GlassCard from "../ui/GlassCard";

export default function Hero() {
  return (
    <section className="grid items-center gap-12 py-20 lg:grid-cols-2 lg:py-28">

      <div>
        <div className="mb-6 inline-flex items-center gap-2 rounded-full
          bg-purple-100 px-4 py-2 text-xs font-bold text-[#5535A5]">
          <Sparkles size={15} />
          The smarter way to freelance
        </div>

        <h1 className="text-5xl font-extrabold leading-tight tracking-tight
          text-[#242036] sm:text-6xl">
          Freelancing,
          <span className="block text-[#7653D6]">
            Without the
          </span>
          Uncertainty.
        </h1>

        <p className="mt-6 max-w-xl text-lg leading-8 text-[#858096]">
          Plan projects with AI, agree on clear milestones,
          communicate in one secure workspace and manage
          payments with confidence.
        </p>

        <div className="mt-8 flex flex-wrap gap-4">
          <Button onClick={() => window.location.assign("/client/register")}>
            Find a Freelancer <ArrowRight size={18} />
          </Button>

          <Button
            variant="secondary"
            onClick={() => window.location.assign("/freelancer/register")}
          >
            Start Freelancing
          </Button>
        </div>

        <div className="mt-8 flex flex-wrap gap-5 text-sm text-[#858096]">
          <span className="flex items-center gap-2">
            <CircleCheck size={17} className="text-[#7653D6]" />
            AI-powered planning
          </span>

          <span className="flex items-center gap-2">
            <ShieldCheck size={17} className="text-[#7653D6]" />
            Structured payments
          </span>
        </div>
      </div>

      <GlassCard className="relative overflow-hidden p-8">
        <div className="absolute -right-16 -top-16 h-52 w-52
          rounded-full bg-purple-200/50 blur-3xl" />

        <div className="relative space-y-5">
          <div className="flex items-center justify-between">
            <span className="font-bold text-[#242036]">
              Project Overview
            </span>
            <span className="rounded-full bg-purple-100 px-3 py-1
              text-xs font-semibold text-[#5535A5]">
              AI assisted
            </span>
          </div>

          <div className="rounded-2xl bg-purple-50 p-5">
            <Sparkles className="mb-3 text-[#7653D6]" />
            <h3 className="font-bold text-[#242036]">
              Project roadmap generated
            </h3>
            <p className="mt-2 text-sm text-[#858096]">
              Scope, deliverables and milestones organized
              into a structured agreement.
            </p>
          </div>

          {["Project scope approved", "Milestone agreement", "Payment authorization"].map((item) => (
            <div key={item} className="flex items-center gap-3 rounded-xl
              border border-purple-100 bg-white p-4">
              <CircleCheck className="text-[#7653D6]" size={19} />
              <span className="text-sm font-semibold text-[#242036]">
                {item}
              </span>
            </div>
          ))}
        </div>
      </GlassCard>

    </section>
  );
}