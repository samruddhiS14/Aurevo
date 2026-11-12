import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function ProtectedRoute({ allowedRole, role, children }) {
  const { user, loading } = useAuth();
  const requiredRole = (allowedRole || role || "").toUpperCase();
  if (loading) return <div className="flex min-h-screen items-center justify-center text-violet-700">Verifying your account...</div>;
  if (!user) return <Navigate to={requiredRole === "ADMIN" ? "/admin/login" : requiredRole === "CLIENT" ? "/client/login" : "/freelancer/login"} replace />;
  if (requiredRole && user.role !== requiredRole) return <Navigate to={user.role === "ADMIN" ? "/admin/dashboard" : user.role === "CLIENT" ? "/client/dashboard" : "/freelancer/dashboard"} replace />;
  return children;
}
