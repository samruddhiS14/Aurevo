import { ShieldCheck, LockKeyhole, Clock3 } from "lucide-react";

export default function PaymentSecurity() {
  return (
    <section id="security" className="py-24">
      <div className="grid items-center gap-12 lg:grid-cols-2">
        <div>
          <p className="font-bold text-[#7653D6]">PAYMENT TRANSPARENCY</p>

          <h2 className="mt-4 text-4xl font-extrabold text-[#242036]">
            Payments with clear rules.
          </h2>

          <p className="mt-5 leading-8 text-[#858096]">
            Keep payment terms connected to project agreements,
            deliverables and milestone approvals.
          </p>

          <div className="mt-8 space-y-5">
            {[
              [LockKeyhole, "Planned PayPal integration", "Designed for future PayPal authorization and capture."],
              [Clock3, "Approval tracking", "Track submission and approval deadlines."],
              [ShieldCheck, "Clear agreements", "Keep scope and payment terms documented."],
            ].map(([Icon, title, description]) => (
              <div key={title} className="flex gap-4">
                <div className="rounded-xl bg-[#EAE3FF] p-3">
                  <Icon className="text-[#7653D6]" />
                </div>
                <div>
                  <h3 className="font-bold text-[#242036]">{title}</h3>
                  <p className="mt-1 text-sm text-[#858096]">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl bg-gradient-to-br from-[#7653D6] to-[#5535A5] p-9 text-white shadow-xl">
          <ShieldCheck size={45} />
          <h3 className="mt-6 text-3xl font-bold">
            Clarity at every milestone.
          </h3>
          <p className="mt-4 leading-7 text-purple-100">
            The planned flow treats authorization, submission, approval and capture
            as distinct payment lifecycle events.
          </p>
          <div className="mt-8 rounded-2xl bg-white/15 p-5 backdrop-blur">
            <p className="text-sm font-semibold">Planned payment workflow</p>
            <p className="mt-2 text-sm text-purple-100">
              Authorization → Work submission → Approval → Capture
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}