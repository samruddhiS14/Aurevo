import apiClient from "./apiClient";

export async function getBackendHealth() {
  const { data } = await apiClient.get("/api/health");
  return data;
}
