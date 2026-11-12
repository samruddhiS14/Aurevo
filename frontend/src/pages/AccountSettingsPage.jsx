import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function AccountSettingsPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [payments, setPayments] = useState([]);
  const [password, setPassword] = useState({ current_password: "", new_password: "" });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError("");

    const requests = await Promise.allSettled([
      api.get("/api/v1/account/profile"),
      api.get("/api/v1/notifications"),
      api.get("/api/v1/account/reviews"),
      // The PayPal router is mounted under /api and exposes GET /payments/mine.
      api.get("/api/payments/mine"),
    ]);

    const [profileResult, notificationsResult, reviewsResult, paymentsResult] = requests;

    if (profileResult.status !== "fulfilled") {
      setError(profileResult.reason?.response?.data?.detail || "Your profile could not be loaded. Please try again.");
      setLoading(false);
      return;
    }

    setProfile(profileResult.value.data);
    setNotifications(notificationsResult.status === "fulfilled" ? notificationsResult.value.data : []);
    setReviews(reviewsResult.status === "fulfilled" ? reviewsResult.value.data : []);
    setPayments(paymentsResult.status === "fulfilled" ? paymentsResult.value.data : []);

    const failedSections = [];
    if (notificationsResult.status !== "fulfilled") failedSections.push("notifications");
    if (reviewsResult.status !== "fulfilled") failedSections.push("reviews");
    if (paymentsResult.status !== "fulfilled") failedSections.push("payment history");
    if (failedSections.length) {
      setError(`Your profile loaded, but ${failedSections.join(", ")} could not be loaded. Refresh to try again.`);
    }

    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const updateProfile = async (event) => {
    event.preventDefault();
    try {
      const body = {
        ...profile.profile,
        full_name: profile.full_name,
        country: profile.country,
      };
      const { data } = await api.patch("/api/v1/account/profile", body);
      setProfile(data);
      setMessage("Profile updated.");
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Profile update failed.");
    }
  };

  const updatePassword = async (event) => {
    event.preventDefault();
    try {
      await api.post("/api/v1/account/password", password);
      setPassword({ current_password: "", new_password: "" });
      setMessage("Password updated. Please sign in again.");
      setError("");
      logout();
      navigate(user?.role === "CLIENT" ? "/client/login" : "/freelancer/login", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || "Password update failed.");
    }
  };

  const read = async (id) => {
    try {
      await api.post(`/api/v1/notifications/${id}/read`);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update notification.");
    }
  };

  const readAll = async () => {
    try {
      await api.post("/api/v1/notifications/read-all");
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not update notifications.");
    }
  };

  if (loading && !profile) {
    return <main className="min-h-screen bg-[#f8f7ff] p-8">Loading account…</main>;
  }

  if (!profile) {
    return (
      <main className="min-h-screen bg-[#f8f7ff] p-8">
        <p className="rounded-xl bg-red-50 p-4 text-sm text-red-700" role="alert">{error || "Account data could not be loaded."}</p>
        <button onClick={load} className="mt-4 rounded-xl bg-violet-700 px-4 py-2 text-sm font-semibold text-white">Try again</button>
      </main>
    );
  }

  const profileFields = [
    ["full_name", "Full name"],
    ["country", "Country"],
    ...(profile.role === "CLIENT"
      ? [["company_name", "Company name"]]
      : [["professional_title", "Professional title"], ["skills", "Skills"], ["experience_years", "Years of experience"]]),
  ];

  return (
    <main className="min-h-screen bg-[#f8f7ff] px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <Link to={user?.role === "CLIENT" ? "/client/dashboard" : "/freelancer/dashboard"} className="text-sm font-semibold text-violet-700">← Dashboard</Link>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-bold text-slate-900">Account & settings</h1>
          <button onClick={load} disabled={loading} className="rounded-xl border border-violet-200 px-3 py-2 text-sm font-semibold text-violet-700 disabled:opacity-50">{loading ? "Refreshing…" : "Refresh"}</button>
        </div>
        {message && <p className="rounded-xl bg-green-50 p-3 text-sm text-green-700">{message}</p>}
        {error && <p className="rounded-xl bg-amber-50 p-3 text-sm text-amber-800" role="alert">{error}</p>}

        <div className="grid gap-6 md:grid-cols-2">
          <section className="rounded-2xl border border-violet-100 bg-white p-6">
            <h2 className="font-bold">Profile</h2>
            <form onSubmit={updateProfile} className="mt-4 space-y-3">
              {profileFields.map(([key, label]) => (
                <label key={key} className="block text-sm font-medium text-slate-600">
                  {label}
                  <input
                    type={key === "experience_years" ? "number" : "text"}
                    value={key in profile ? profile[key] ?? "" : profile.profile?.[key] ?? ""}
                    onChange={(event) => setProfile((current) => key in current
                      ? { ...current, [key]: event.target.value }
                      : { ...current, profile: { ...current.profile, [key]: event.target.value } })}
                    className="mt-1 w-full rounded-xl border border-slate-200 p-2.5"
                  />
                </label>
              ))}
              <p className="text-xs text-slate-500">{profile.email} · {profile.role} · Rating {profile.average_rating?.toFixed?.(1) ?? "—"} ({profile.review_count} reviews)</p>
              <button className="rounded-xl bg-violet-700 px-4 py-2.5 text-sm font-semibold text-white">Save profile</button>
            </form>
          </section>

          <section className="rounded-2xl border border-violet-100 bg-white p-6">
            <h2 className="font-bold">Change password</h2>
            <form onSubmit={updatePassword} className="mt-4 space-y-3">
              <input type="password" autoComplete="current-password" placeholder="Current password" value={password.current_password} onChange={(event) => setPassword((current) => ({ ...current, current_password: event.target.value }))} className="w-full rounded-xl border border-slate-200 p-3" required />
              <input type="password" autoComplete="new-password" minLength={10} placeholder="New password (10+ characters)" value={password.new_password} onChange={(event) => setPassword((current) => ({ ...current, new_password: event.target.value }))} className="w-full rounded-xl border border-slate-200 p-3" required />
              <button className="rounded-xl border border-violet-200 px-4 py-2.5 text-sm font-semibold text-violet-700">Update password</button>
            </form>
            <p className="mt-3 text-xs text-slate-500">Your email address is read-only here. Password changes are checked on the backend.</p>
          </section>
        </div>

        <section className="rounded-2xl border border-violet-100 bg-white p-6">
          <div className="flex items-center justify-between gap-3"><h2 className="font-bold">Notifications</h2><button onClick={readAll} className="text-sm font-semibold text-violet-700">Mark all read</button></div>
          <div className="mt-4 space-y-3">
            {notifications.map((notification) => (
              <div key={notification.id} className={`rounded-xl p-3 ${notification.is_read ? "bg-slate-50" : "bg-violet-50"}`}>
                <div className="flex justify-between gap-3"><p className="font-semibold text-slate-800">{notification.title}</p>{!notification.is_read && <button onClick={() => read(notification.id)} className="text-xs font-semibold text-violet-700">Mark read</button>}</div>
                <p className="mt-1 text-sm text-slate-600">{notification.message}</p>
                <p className="mt-1 text-[11px] text-slate-400">{new Date(notification.created_at).toLocaleString()}</p>
              </div>
            ))}
            {!notifications.length && <p className="text-sm text-slate-500">No notifications to display.</p>}
          </div>
        </section>

        <section className="rounded-2xl border border-violet-100 bg-white p-6">
          <h2 className="font-bold">PayPal milestone payment history</h2>
          <div className="mt-3 space-y-3">
            {payments.map((payment) => (
              <div key={payment.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-3">
                <div>
                  <p className="font-semibold text-slate-800">{payment.milestone_title || `Milestone #${payment.milestone_id}`}</p>
                  <p className="text-xs text-slate-500">{payment.project_title || `Project #${payment.project_id}`} · {payment.status || "Status unavailable"}</p>
                  <p className="text-[11px] text-slate-400">{payment.created_at ? new Date(payment.created_at).toLocaleString() : "Date unavailable"}</p>
                  {payment.paypal_amount && payment.paypal_currency && (payment.paypal_currency !== payment.currency || payment.paypal_amount !== payment.amount) && <p className="mt-1 text-xs text-slate-600">PayPal quote: {payment.paypal_currency} {payment.paypal_amount}{payment.exchange_rate ? ` · Rate ${payment.exchange_rate} (${payment.exchange_rate_date || "date unavailable"})` : ""}</p>}
                  {payment.failure_reason && <p className="mt-1 text-xs text-amber-700">Attention: {payment.failure_reason}</p>}
                </div>
                <p className="font-semibold text-slate-800">{payment.currency} {payment.amount}</p>
              </div>
            ))}
            {!payments.length && <p className="text-sm text-slate-500">No PayPal milestone payments yet.</p>}
          </div>
        </section>

        <section className="rounded-2xl border border-violet-100 bg-white p-6">
          <h2 className="font-bold">Received reviews</h2>
          <div className="mt-3 space-y-3">
            {reviews.map((review) => (
              <div key={review.id} className="border-b border-slate-100 pb-3">
                <p className="font-semibold text-amber-600">{"★".repeat(review.rating)}{"☆".repeat(5 - review.rating)}</p>
                <p className="mt-1 text-sm text-slate-700">{review.comment || "No written comment."}</p>
              </div>
            ))}
            {!reviews.length && <p className="text-sm text-slate-500">No reviews to display yet.</p>}
          </div>
        </section>
      </div>
    </main>
  );
}
