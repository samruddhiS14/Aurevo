
export function DashboardLoading() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {[1, 2, 3, 4].map((item) => (
        <div
          key={item}
          className="h-32 animate-pulse rounded-2xl bg-violet-100"
        />
      ))}
    </div>
  );
}

export function DashboardError({ message, onRetry }) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-6">
      <h3 className="font-semibold text-red-800">
        Dashboard could not be loaded
      </h3>
      <p className="mt-2 text-sm text-red-700">{message}</p>
      <button
        onClick={onRetry}
        className="mt-4 rounded-xl bg-red-700 px-4 py-2
          text-sm font-semibold text-white hover:bg-red-800"
      >
        Try again
      </button>
    </div>
  );
}

export function EmptyState({ title, message }) {
  return (
    <div className="rounded-2xl border border-dashed border-violet-200
      bg-white p-8 text-center">
      <h3 className="font-semibold text-slate-800">{title}</h3>
      <p className="mt-2 text-sm text-slate-500">{message}</p>
    </div>
  );
}
