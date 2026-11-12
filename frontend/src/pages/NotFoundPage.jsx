import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-[#F8F7FC] p-6">
      <h1 className="text-4xl font-bold text-[#7653D6]">404</h1>
      <p className="mt-3 text-[#625D70]">This page could not be found.</p>
      <Link to="/" className="mt-5 text-[#7653D6] font-semibold">
        Return home
      </Link>
    </main>
  );
}