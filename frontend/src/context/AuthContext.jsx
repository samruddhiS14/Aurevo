import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { getCurrentUser } from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const onSessionExpired = () => setUser(null);
    window.addEventListener("aurevo:session-expired", onSessionExpired);
    const token = sessionStorage.getItem("access_token");

    if (!token) {
      setLoading(false);
      return () => window.removeEventListener("aurevo:session-expired", onSessionExpired);
    }

    getCurrentUser(token)
      .then(setUser)
      .catch(() => {
        sessionStorage.removeItem("access_token");
        setUser(null);
      })
      .finally(() => setLoading(false));
    return () => window.removeEventListener("aurevo:session-expired", onSessionExpired);
  }, []);

  function saveSession(authData) {
    sessionStorage.setItem("access_token", authData.access_token);
    setUser(authData.user);
  }

  function logout() {
    sessionStorage.removeItem("access_token");
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, saveSession, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}