import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

function rowsFor(label, totals) {
  if (Array.isArray(totals)) return totals.map((item) => ({ name: `${label} ${item.currency}`, amount: Number(item.amount || 0), currency: item.currency }));
  return [{ name: label, amount: Number(totals || 0), currency: "USD" }];
}

export default function PaymentChart({ authorized = [], captured = [] }) {
  const data = [...rowsFor("Authorized", authorized), ...rowsFor("Captured", captured)];
  return (
    <div className="rounded-2xl border border-violet-100 bg-white p-6 shadow-sm">
      <h2 className="text-lg font-bold text-slate-900">PayPal Payment Overview</h2>
      <p className="mb-5 text-sm text-slate-500">Amounts are grouped by currency; different currencies are never added together.</p>
      {data.length ? <div className="h-64 w-full"><ResponsiveContainer width="100%" height="100%"><BarChart data={data}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="name" /><YAxis /><Tooltip formatter={(value, _name, item) => [`${item.payload.currency} ${Number(value).toFixed(2)}`, "Amount"]} /><Bar dataKey="amount" fill="#7c3aed" radius={[8, 8, 0, 0]} /></BarChart></ResponsiveContainer></div> : <p className="rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-500">No PayPal authorization or capture records yet.</p>}
    </div>
  );
}
