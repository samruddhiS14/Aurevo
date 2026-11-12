import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { authorizePayPalOrder } from "../../services/paypalService";

export default function PayPalSuccess() {
  const [searchParams] = useSearchParams();
  const orderId =
    searchParams.get("token") || searchParams.get("order_id");

  const [status, setStatus] = useState("processing");
  const [message, setMessage] = useState(
    "Verifying your PayPal approval..."
  );

  const requestStarted = useRef(false);

  useEffect(() => {
    if (!orderId) {
      setStatus("error");
      setMessage("PayPal did not return a valid order ID.");
      return;
    }

    if (requestStarted.current) return;
    requestStarted.current = true;

    const authorizePayment = async () => {
      try {
        const result = await authorizePayPalOrder(orderId);

        setStatus("success");
        setMessage(
          result.message ||
            "Your PayPal authorization was successfully verified."
        );
      } catch (error) {
        setStatus("error");
        setMessage(
          error.response?.data?.detail ||
            "We could not verify the PayPal authorization. Please check your payment history before retrying."
        );
      }
    };

    authorizePayment();
  }, [orderId]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#F4F0FF] to-[#EAE4FA] px-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-8 text-center shadow-xl">
        {status === "processing" && (
          <div className="mx-auto mb-5 h-12 w-12 animate-spin rounded-full border-4 border-purple-200 border-t-purple-700" />
        )}

        {status === "success" && (
          <div className="mb-5 text-5xl text-green-600">✓</div>
        )}

        {status === "error" && (
          <div className="mb-5 text-5xl text-red-500">!</div>
        )}

        <h1 className="mb-3 text-2xl font-bold text-gray-900">
          {status === "processing"
            ? "Verifying Payment"
            : status === "success"
              ? "Authorization Successful"
              : "Authorization Could Not Be Verified"}
        </h1>

        <p className="mb-6 text-gray-600">{message}</p>

        {status !== "processing" && (
          <Link
            to="/client/dashboard"
            className="inline-block rounded-xl bg-[#6C4AB6] px-6 py-3 font-semibold text-white hover:bg-[#58399E]"
          >
            Return to Dashboard
          </Link>
        )}

        <p className="mt-5 break-all text-xs text-gray-400">
          Order ID: {orderId || "Unavailable"}
        </p>
      </div>
    </div>
  );
}