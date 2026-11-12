import { X } from "lucide-react";

export default function Modal({
  open,
  onClose,
  title,
  children,
}) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center
      bg-[#242036]/40 p-4 backdrop-blur-sm"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl"
      >
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-xl font-bold text-[#242036]">
            {title}
          </h2>

          <button
            onClick={onClose}
            aria-label="Close modal"
            className="rounded-lg p-2 hover:bg-purple-50"
          >
            <X size={20} />
          </button>
        </div>

        {children}
      </div>
    </div>
  );
}