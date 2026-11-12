const styles = {
  success: "bg-green-50 text-green-700",
  pending: "bg-amber-50 text-amber-700",
  danger: "bg-red-50 text-red-700",
  info: "bg-purple-50 text-purple-700",
};

export default function StatusBadge({
  children,
  status = "info",
}) {
  return (
    <span
      className={`
        inline-flex items-center rounded-full
        px-3 py-1 text-xs font-semibold
        ${styles[status]}
      `}
    >
      {children}
    </span>
  );
}