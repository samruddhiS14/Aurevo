import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff, UserPlus } from "lucide-react";

import { useAuth } from "../../context/AuthContext";
import {
  registerClient,
  registerFreelancer,
} from "../../services/authService";

export default function RegisterPage({ role }) {
  const isClient = role === "CLIENT";
  const navigate = useNavigate();
  const { saveSession } = useAuth();

  const [form, setForm] = useState({
    full_name: "",
    company_name: "",
    email: "",
    password: "",
    confirm_password: "",
    country: "",
    professional_title: "",
    skills: "",
    experience_years: "0",
    terms_accepted: false,
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function updateField(event) {
    const { name, value, type, checked } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    if (form.password !== form.confirm_password) {
      setError("Your passwords do not match.");
      return;
    }

    if (form.password.length < 10) {
      setError("Use a password with at least 10 characters.");
      return;
    }

    if (!form.terms_accepted) {
      setError("Please accept the terms and conditions.");
      return;
    }

    if (!isClient && !form.skills.trim()) {
      setError("Please enter at least one professional skill.");
      return;
    }

    setSubmitting(true);

    try {
      let result;

      if (isClient) {
        result = await registerClient({
          full_name: form.full_name.trim(),
          company_name: form.company_name.trim() || null,
          email: form.email.trim(),
          password: form.password,
          confirm_password: form.confirm_password,
          country: form.country,
          terms_accepted: form.terms_accepted,
        });
      } else {
        result = await registerFreelancer({
          full_name: form.full_name.trim(),
          email: form.email.trim(),
          password: form.password,
          confirm_password: form.confirm_password,
          country: form.country,
          professional_title: form.professional_title.trim(),
          skills: form.skills
            .split(",")
            .map((skill) => skill.trim())
            .filter(Boolean),
          experience_years: Number(form.experience_years),
          terms_accepted: form.terms_accepted,
        });
      }

      saveSession(result);

      navigate(
        isClient ? "/client/dashboard" : "/freelancer/dashboard",
        { replace: true }
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Registration failed. Please check your details and try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-xl border border-[#E4DFF0] bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-[#B9A5F5]";

  function PasswordField({ name, label, visible, toggle }) {
    return (
      <div>
        <label htmlFor={name} className="block text-sm font-medium mb-2">
          {label}
        </label>

        <div className="relative">
          <input
            id={name}
            name={name}
            type={visible ? "text" : "password"}
            required
            minLength={10}
            maxLength={128}
            autoComplete={
              name === "password" ? "new-password" : "new-password"
            }
            value={form[name]}
            onChange={updateField}
            className={`${inputClass} pr-12`}
            placeholder={`Enter ${label.toLowerCase()}`}
          />

          <button
            type="button"
            onClick={toggle}
            aria-label={visible ? "Hide password" : "Show password"}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-[#858096]"
          >
            {visible ? <EyeOff size={19} /> : <Eye size={19} />}
          </button>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#F8F7FC] px-5 py-12">
      <div className="max-w-2xl mx-auto">
        <Link to="/" className="block text-center mb-8">
          <span className="text-3xl font-extrabold text-[#7653D6]">
            Aurevo
          </span>
          <span className="block text-sm text-[#858096] mt-1">
            Create your {isClient ? "client" : "freelancer"} account
          </span>
        </Link>

        <section className="bg-white/90 border border-[#EAE3FF] rounded-3xl shadow-xl shadow-purple-100/60 p-7 sm:p-9">
          <div className="w-12 h-12 rounded-2xl bg-[#EAE3FF] flex items-center justify-center mb-5">
            <UserPlus className="text-[#7653D6]" size={24} />
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-[#242036]">
            Create {isClient ? "Client" : "Freelancer"} Account
          </h1>

          <p className="text-sm text-[#858096] mt-2 mb-7">
            {isClient
              ? "Set up your account to publish projects and hire talent."
              : "Create your profile to showcase your skills and find projects."}
          </p>

          <form onSubmit={handleSubmit} className="grid sm:grid-cols-2 gap-5">
            <div className="sm:col-span-2">
              <label htmlFor="full_name" className="block text-sm font-medium mb-2">
                Full name
              </label>
              <input
                id="full_name"
                name="full_name"
                required
                minLength={2}
                maxLength={150}
                autoComplete="name"
                value={form.full_name}
                onChange={updateField}
                className={inputClass}
                placeholder="Your full name"
              />
            </div>

            {isClient && (
              <div className="sm:col-span-2">
                <label htmlFor="company_name" className="block text-sm font-medium mb-2">
                  Company name <span className="text-[#858096]">(optional)</span>
                </label>
                <input
                  id="company_name"
                  name="company_name"
                  maxLength={180}
                  value={form.company_name}
                  onChange={updateField}
                  className={inputClass}
                  placeholder="Your company or organization"
                />
              </div>
            )}

            <div className="sm:col-span-2">
              <label htmlFor="email" className="block text-sm font-medium mb-2">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                autoComplete="email"
                value={form.email}
                onChange={updateField}
                className={inputClass}
                placeholder="you@example.com"
              />
            </div>

            <PasswordField
              name="password"
              label="Password"
              visible={showPassword}
              toggle={() => setShowPassword((value) => !value)}
            />

            <PasswordField
              name="confirm_password"
              label="Confirm password"
              visible={showConfirmPassword}
              toggle={() => setShowConfirmPassword((value) => !value)}
            />

            <div className="sm:col-span-2">
              <label htmlFor="country" className="block text-sm font-medium mb-2">
                Country
              </label>
              <input
                id="country"
                name="country"
                required
                minLength={2}
                maxLength={100}
                autoComplete="country-name"
                value={form.country}
                onChange={updateField}
                className={inputClass}
                placeholder="Enter your country"
              />
            </div>

            {!isClient && (
              <>
                <div className="sm:col-span-2">
                  <label htmlFor="professional_title" className="block text-sm font-medium mb-2">
                    Professional title
                  </label>
                  <input
                    id="professional_title"
                    name="professional_title"
                    required
                    minLength={2}
                    maxLength={180}
                    value={form.professional_title}
                    onChange={updateField}
                    className={inputClass}
                    placeholder="e.g. Full-Stack Developer"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label htmlFor="skills" className="block text-sm font-medium mb-2">
                    Skills
                  </label>
                  <input
                    id="skills"
                    name="skills"
                    required
                    value={form.skills}
                    onChange={updateField}
                    className={inputClass}
                    placeholder="React, Python, UI/UX Design"
                  />
                  <p className="text-xs text-[#858096] mt-2">
                    Separate skills with commas.
                  </p>
                </div>

                <div className="sm:col-span-2">
                  <label htmlFor="experience_years" className="block text-sm font-medium mb-2">
                    Experience (years)
                  </label>
                  <input
                    id="experience_years"
                    name="experience_years"
                    type="number"
                    required
                    min="0"
                    max="60"
                    step="1"
                    value={form.experience_years}
                    onChange={updateField}
                    className={inputClass}
                  />
                </div>
              </>
            )}

            <label className="sm:col-span-2 flex items-start gap-3 text-sm text-[#625D70]">
              <input
                type="checkbox"
                name="terms_accepted"
                checked={form.terms_accepted}
                onChange={updateField}
                className="mt-1 accent-[#7653D6]"
              />
              <span>
                I agree to the Terms of Service and Privacy Policy.
              </span>
            </label>

            {error && (
              <p role="alert" className="sm:col-span-2 text-sm text-red-600">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="sm:col-span-2 w-full rounded-xl bg-gradient-to-r from-[#7653D6] to-[#5535A5] text-white font-semibold py-3.5 shadow-lg shadow-purple-200 hover:opacity-95 disabled:opacity-60 transition"
            >
              {submitting ? "Creating account..." : "Create Account"}
            </button>
          </form>

          <p className="text-center text-sm text-[#625D70] mt-6">
            Already have an account?{" "}
            <Link
              to={isClient ? "/client/login" : "/freelancer/login"}
              className="text-[#7653D6] font-semibold hover:underline"
            >
              Sign In
            </Link>
          </p>
        </section>

        <p className="text-center text-sm text-[#858096] mt-6">
          {isClient ? "Looking to work on projects?" : "Looking to hire talent?"}{" "}
          <Link
            to={isClient ? "/freelancer/register" : "/client/register"}
            className="text-[#7653D6] font-semibold hover:underline"
          >
            {isClient ? "Join as a Freelancer" : "Create a Client Account"}
          </Link>
        </p>
      </div>
    </main>
  );
}