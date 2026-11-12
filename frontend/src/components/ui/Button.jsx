import { LoaderCircle } from "lucide-react";

const variants = {
  primary:
    "bg-[#7653D6] text-white hover:bg-[#5535A5] shadow-lg shadow-purple-200",
  secondary:
    "bg-[#EAE3FF] text-[#5535A5] hover:bg-[#DDD0FF]",
  outline:
    "border border-[#E5DDF7] bg-white text-[#5535A5] hover:bg-[#F8F5FF]",
  ghost:
    "text-[#7653D6] hover:bg-[#F1ECFF]",
};

export default function Button({
  children,
  variant = "primary",
  loading = false,
  className = "",
  ...props
}) {
  return (
    <button
      {...props}
      disabled={loading || props.disabled}
      className={`
        inline-flex items-center justify-center gap-2
        rounded-xl px-6 py-3
        text-sm font-semibold
        transition-all duration-300
        hover:-translate-y-0.5
        disabled:opacity-50 disabled:cursor-not-allowed
        ${variants[variant]}
        ${className}
      `}
    >
      {loading && <LoaderCircle size={17} className="animate-spin" />}
      {children}
    </button>
  );
}