import { Link } from "react-router-dom";

export default function PayPalCancel() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#F4F0FF] to-[#EAE4FA] px-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-8 text-center shadow-xl">
        <div className="mb-5 text-5xl text-amber-500">!</div>

        <h1 className="mb-3 text-2xl font-bold text-gray-900">
          Payment Cancelled
        </h1>

        <p className="mb-6 text-gray-600">
          You cancelled the PayPal approval process. No successful
          authorization has been confirmed.
        </p>

        <Link
          to="/client/dashboard"
          className="inline-block rounded-xl bg-[#6C4AB6] px-6 py-3 font-semibold text-white hover:bg-[#58399E]"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}