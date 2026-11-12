import { Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import LoginPage from "./components/auth/LoginPage";
import RegisterPage from "./components/auth/RegisterPage";
import LandingPage from "./pages/LandingPage";
import NotFoundPage from "./pages/NotFoundPage";
import ClientDashboard from "./pages/client/ClientDashboard";
import FreelancerDashboard from "./pages/freelancer/FreelancerDashboard";
import PayPalSuccess from "./pages/payments/PayPalSuccess";
import PayPalCancel from "./pages/payments/PayPalCancel";
import ProjectsPage from "./pages/ProjectsPage";
import CreateProjectPage from "./pages/CreateProjectPage";
import ProjectApplicationsPage from "./pages/ProjectApplicationsPage";
import ProjectWorkspace from "./pages/ProjectWorkspace";
import AccountSettingsPage from "./pages/AccountSettingsPage";
import FreelancerApplicationsPage from "./pages/FreelancerApplicationsPage";
import AdminDashboard from "./pages/admin/AdminDashboard";

export default function App() {
  return <AuthProvider><Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/client/login" element={<LoginPage role="CLIENT" />} />
    <Route path="/client/register" element={<RegisterPage role="CLIENT" />} />
    <Route path="/freelancer/login" element={<LoginPage role="FREELANCER" />} />
    <Route path="/freelancer/register" element={<RegisterPage role="FREELANCER" />} />
    <Route path="/admin/login" element={<LoginPage role="ADMIN" />} />
    <Route path="/admin/dashboard" element={<ProtectedRoute allowedRole="ADMIN"><AdminDashboard /></ProtectedRoute>} />

    <Route path="/client/dashboard" element={<ProtectedRoute allowedRole="CLIENT"><ClientDashboard /></ProtectedRoute>} />
    <Route path="/freelancer/dashboard" element={<ProtectedRoute allowedRole="FREELANCER"><FreelancerDashboard /></ProtectedRoute>} />
    <Route path="/client/projects" element={<ProtectedRoute allowedRole="CLIENT"><ProjectsPage /></ProtectedRoute>} />
    <Route path="/client/projects/create" element={<ProtectedRoute allowedRole="CLIENT"><CreateProjectPage /></ProtectedRoute>} />
    <Route path="/client/projects/:projectId/applications" element={<ProtectedRoute allowedRole="CLIENT"><ProjectApplicationsPage /></ProtectedRoute>} />
    <Route path="/client/projects/:projectId/workspace" element={<ProtectedRoute allowedRole="CLIENT"><ProjectWorkspace /></ProtectedRoute>} />
    <Route path="/freelancer/projects" element={<ProtectedRoute allowedRole="FREELANCER"><ProjectsPage /></ProtectedRoute>} />
    <Route path="/freelancer/applications" element={<ProtectedRoute allowedRole="FREELANCER"><FreelancerApplicationsPage /></ProtectedRoute>} />
    <Route path="/freelancer/projects/:projectId/workspace" element={<ProtectedRoute allowedRole="FREELANCER"><ProjectWorkspace /></ProtectedRoute>} />
    <Route path="/client/account" element={<ProtectedRoute allowedRole="CLIENT"><AccountSettingsPage /></ProtectedRoute>} />
    <Route path="/freelancer/account" element={<ProtectedRoute allowedRole="FREELANCER"><AccountSettingsPage /></ProtectedRoute>} />

    <Route path="/paypal/success" element={<PayPalSuccess />} />
    <Route path="/paypal/cancel" element={<PayPalCancel />} />
    <Route path="*" element={<NotFoundPage />} />
  </Routes></AuthProvider>;
}
