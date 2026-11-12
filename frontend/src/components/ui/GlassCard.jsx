export default function GlassCard({
  children,
  className = "",
}) {
  return (
    <div
      className={`
        rounded-2xl
        border border-white/80
        bg-white/75
        shadow-[0_12px_40px_rgba(91,58,150,0.08)]
        backdrop-blur-xl
        transition duration-300
        hover:-translate-y-1
        hover:shadow-[0_18px_50px_rgba(91,58,150,0.13)]
        ${className}
      `}
    >
      {children}
    </div>
  );
}