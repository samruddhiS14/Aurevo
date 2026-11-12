import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function DashboardPlaceholder({ role }) {
  const { user, logout } = useAuth();

  const isClient = role === "CLIENT";

  return (
    <main className="min-h-screen bg-[#F8F7FC] p-8">
      <div className="max-w-3xl mx-auto bg-white border border-[#EAE3FF] rounded-3xl p-8 shadow-lg">
        <p className="text-sm text-[#7653D6] font-semibold">
          {isClient ? "CLIENT PORTAL" : "FREELANCER PORTAL"}
        </p>

        <h1 className="text-3xl font-bold text-[#242036] mt-3">
          Welcome, {user?.full_name}
        </h1>

        <p className="text-[#858096] mt-2">
          Your {isClient ? "client" : "freelancer"} dashboard will be developed
          in a later phase.
        </p>

        <button
          onClick={logout}
          className="mt-6 rounded-xl bg-[#7653D6] text-white px-5 py-3"
        >
          Sign Out
        </button>

        <Link to="/" className="block mt-5 text-[#7653D6]">
          Back to home
        </Link>
      </div>
    </main>
  );
}