import axios from "axios";

const API_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const authApi = axios.create({
  baseURL: `${API_URL}/api/v1/auth`,
  headers: {
    "Content-Type": "application/json",
  },
});

export async function registerClient(payload) {
  const { data } = await authApi.post("/client/register", payload);
  return data;
}

export async function registerFreelancer(payload) {
  const { data } = await authApi.post("/freelancer/register", payload);
  return data;
}

export async function loginClient(payload) {
  const { data } = await authApi.post("/client/login", payload);
  return data;
}

export async function loginFreelancer(payload) {
  const { data } = await authApi.post("/freelancer/login", payload);
  return data;
}

export async function loginAdmin(payload) {
  const { data } = await authApi.post("/admin/login", payload);
  return data;
}

export async function getCurrentUser(token) {
  const { data } = await authApi.get("/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return data;
}