const testimonials = [
  {
    quote: "The structured project workflow makes expectations much clearer.",
    name: "Illustrative Client",
    role: "Sample testimonial · Not a real user",
  },
  {
    quote: "Having milestones and communication together would make projects easier to manage.",
    name: "Illustrative Freelancer",
    role: "Sample testimonial · Not a real user",
  },
];

export default function Testimonials() {
  return (
    <section className="py-24">
      <div className="text-center">
        <p className="font-bold text-[#7653D6]">DESIGNED FOR BOTH SIDES</p>
        <h2 className="mt-3 text-4xl font-extrabold text-[#242036]">
          Better collaboration starts here.
        </h2>
        <p className="mt-3 text-xs text-[#858096]">
          Illustrative sample testimonials. These are not actual customer reviews.
        </p>
      </div>

      <div className="mt-10 grid gap-6 md:grid-cols-2">
        {testimonials.map((item) => (
          <div key={item.name} className="rounded-2xl border border-purple-100
            bg-white p-7 shadow-sm">
            <p className="text-lg leading-8 text-[#242036]">
              “{item.quote}”
            </p>
            <div className="mt-6 border-t border-purple-100 pt-5">
              <p className="font-bold text-[#5535A5]">{item.name}</p>
              <p className="mt-1 text-xs text-[#858096]">{item.role}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}