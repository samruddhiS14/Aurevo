
import { useEffect, useState } from "react";
import {
  getClientDashboard,
  getFreelancerDashboard,
} from "../services/dashboardService";

export default function useDashboard(role) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const result =
          role === "client"
            ? await getClientDashboard()
            : await getFreelancerDashboard();

        if (!cancelled) setData(result);
      } catch (err) {
        if (!cancelled) {
          setError(
            err.response?.data?.detail ||
            "Unable to load your dashboard. Please try again."
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [role]);

  const refresh = () => {
    setData(null);
    setLoading(true);
    setError("");

    const request =
      role === "client"
        ? getClientDashboard()
        : getFreelancerDashboard();

    request
      .then(setData)
      .catch((err) =>
        setError(
          err.response?.data?.detail ||
          "Unable to refresh your dashboard."
        )
      )
      .finally(() => setLoading(false));
  };

  return { data, loading, error, refresh };
}
