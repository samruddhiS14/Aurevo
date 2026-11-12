export default function Input({
  label,
  error,
  className = "",
  ...props
}) {
  return (
    <div className="w-full space-y-2">
      {label && (
        <label className="text-sm font-semibold text-[#242036]">
          {label}
        </label>
      )}

      <input
        {...props}
        className={`
          w-full rounded-xl border
          border-[#E5DDF7]
          bg-white px-4 py-3
          text-sm text-[#242036]
          outline-none transition
          placeholder:text-[#A7A1B5]
          focus:border-[#7653D6]
          focus:ring-4 focus:ring-purple-100
          ${className}
        `}
      />

      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}
    </div>
  );
}