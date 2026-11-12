
import { Link } from "react-router-dom";

export default function StatCard({
  title,
  value,
  description,
  icon: Icon,
  to,
}) {
  const content = (
    <div className="group h-full rounded-2xl border border-violet-100
      bg-white p-5 shadow-sm transition-all duration-200
      hover:-translate-y-1 hover:shadow-lg">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
            {value ?? 0}
          </p>
          {description && (
            <p className="mt-2 text-xs text-slate-500">{description}</p>
          )}
        </div>

        {Icon && (
          <div className="rounded-xl bg-violet-50 p-3 text-violet-700">
            <Icon size={21} />
          </div>
        )}
      </div>
      {to && (
        <p className="mt-4 text-sm font-semibold text-violet-700">
          View details →
        </p>
      )}
    </div>
  );

  return to ? <Link to={to} className="block">{content}</Link> : content;
}

