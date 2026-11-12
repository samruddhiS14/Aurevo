import { useState } from "react";
import { createMilestoneOrder } from "../../services/paypalService";

export default function PayMilestoneButton({ milestoneId }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handlePayment = async () => {
    try {
      setLoading(true);
      setError("");

      const result = await createMilestoneOrder(milestoneId);

      // Use the approval URL returned by your backend
      const approvalUrl =
        result.approval_url ||
        result.links?.find((link) => link.rel === "approve")?.href;

      if (!approvalUrl) {
        throw new Error("PayPal approval URL was not returned.");
      }

      window.location.assign(approvalUrl);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to start PayPal payment."
      );
      setLoading(false);
    }
  };

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={handlePayment}
        disabled={loading}
        className="rounded-xl bg-[#6C4AB6] px-5 py-3 font-semibold text-white shadow-md transition hover:bg-[#58399E] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Connecting to PayPal..." : "Pay with PayPal"}
      </button>

      {error && (
        <p className="text-sm text-red-500" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}