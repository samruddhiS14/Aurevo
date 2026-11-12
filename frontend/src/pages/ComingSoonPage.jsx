import { useLocation, Link } from "react-router-dom";

export default function ComingSoonPage() {
  const location = useLocation();

  const role = location.pathname.includes("/client")
    ? "Client"
    : "Freelancer";

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F8F7FC] p-5">
      <div className="max-w-md rounded-3xl bg-white p-10 text-center shadow-xl">
        <h1 className="text-3xl font-bold text-[#5535A5]">
          {role} Portal
        </h1>

        <p className="mt-4 text-[#858096]">
          This authentication page will be implemented
          in a future development phase.
        </p>

        <Link
          to="/"
          className="mt-7 inline-flex rounded-xl bg-[#7653D6]
          px-6 py-3 font-semibold text-white"
        >
          Return to homepage
        </Link>
      </div>
    </div>
  );
}