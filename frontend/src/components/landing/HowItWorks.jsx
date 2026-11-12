const steps = [
  ["01", "Create a project", "Describe your requirements and goals."],
  ["02", "Agree on milestones", "Review the AI-generated scope and approve terms."],
  ["03", "Complete the work", "Collaborate and submit deliverables."],
  ["04", "Approve and get paid", "Follow the agreed payment workflow."],
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-white py-24">
      <div className="mx-auto max-w-6xl px-5">
        <div className="mb-14 text-center">
          <p className="font-bold text-[#7653D6]">SIMPLE WORKFLOW</p>
          <h2 className="mt-3 text-4xl font-extrabold text-[#242036]">
            From idea to completion.
          </h2>
        </div>

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map(([number, title, description]) => (
            <div key={number} className="rounded-2xl bg-[#F8F7FC] p-6">
              <span className="text-4xl font-extrabold text-[#B9A5F5]">
                {number}
              </span>
              <h3 className="mt-5 font-bold text-[#242036]">{title}</h3>
              <p className="mt-3 text-sm leading-7 text-[#858096]">
                {description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}