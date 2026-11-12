import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";

import { useAuth } from "../../context/AuthContext";
import {
  loginClient,
  loginFreelancer,
  loginAdmin,
} from "../../services/authService";

export default function LoginPage({ role }) {
  const isClient = role === "CLIENT";
  const isAdmin = role === "ADMIN";
  const navigate = useNavigate();
  const { saveSession } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const login = isAdmin ? loginAdmin : isClient ? loginClient : loginFreelancer;
      const result = await login({ email, password });

      if (result.user.role !== role) {
        throw new Error("This account cannot access this portal.");
      }

      saveSession(result);

      navigate(
        isAdmin ? "/admin/dashboard" : isClient ? "/client/dashboard" : "/freelancer/dashboard",
        { replace: true }
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        err.message ||
        "Unable to sign in. Please try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const registerPath = isClient
    ? "/client/register"
    : "/freelancer/register";

  const otherLoginPath = isClient
    ? "/freelancer/login"
    : "/client/login";

  return (
    <main className="min-h-screen bg-[#F8F7FC] flex items-center justify-center px-5 py-12">
      <div className="w-full max-w-md">
        <Link to="/" className="block text-center mb-8">
          <span className="text-3xl font-extrabold text-[#7653D6]">
            Aurevo
          </span>
          <span className="block text-sm text-[#858096] mt-1">
            Work together. Work securely.
          </span>
        </Link>

        <section className="bg-white/90 border border-[#EAE3FF] rounded-3xl shadow-xl shadow-purple-100/60 p-7 sm:p-9">
          <div className="w-12 h-12 rounded-2xl bg-[#EAE3FF] flex items-center justify-center mb-5">
            <ShieldCheck className="text-[#7653D6]" size={25} />
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#242036]">
            Welcome Back, {isAdmin ? "Administrator" : isClient ? "Client" : "Freelancer"}.
          </h1>

          <p className="text-sm text-[#858096] mt-2 mb-7">
            Sign in to continue to your {isAdmin ? "Aurevo administration" : isClient ? "client" : "freelancer"} account.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium mb-2">
                Email
              </label>
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-xl border border-[#E4DFF0] bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-[#B9A5F5]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                Password
              </label>

              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full rounded-xl border border-[#E4DFF0] bg-white px-4 py-3 pr-12 outline-none focus:ring-2 focus:ring-[#B9A5F5]"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#858096]"
                >
                  {showPassword ? <EyeOff size={19} /> : <Eye size={19} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between gap-3 text-sm">
              <label className="flex items-center gap-2 text-[#625D70]">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="accent-[#7653D6]"
                />
                Remember me
              </label>

              <Link
                to="/forgot-password"
                className="text-[#7653D6] font-medium hover:underline"
              >
                Forgot password?
              </Link>
            </div>

            {error && (
              <p role="alert" className="text-sm text-red-600">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-xl bg-gradient-to-r from-[#7653D6] to-[#5535A5] text-white font-semibold py-3.5 shadow-lg shadow-purple-200 hover:opacity-95 disabled:opacity-60 transition"
            >
              {submitting ? "Signing in..." : "Sign In"}
            </button>
          </form>

          {!isAdmin && <p className="text-center text-sm text-[#625D70] mt-6">
            New here?{" "}
            <Link
              to={registerPath}
              className="text-[#7653D6] font-semibold hover:underline"
            >
              Create {isClient ? "Client" : "Freelancer"} Account
            </Link>
          </p>}
        </section>

        {!isAdmin && <p className="text-center text-sm text-[#858096] mt-6">
          {isClient ? "Are you a freelancer?" : "Are you a client?"}{" "}
          <Link
            to={otherLoginPath}
            className="text-[#7653D6] font-semibold hover:underline"
          >
            {isClient ? "Freelancer Login" : "Client Login"}
          </Link>
        </p>}
      </div>
    </main>
  );
}