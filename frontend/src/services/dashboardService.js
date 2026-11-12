
import api from "./api";

export const getClientDashboard = async () => {
  const response = await api.get("/api/v1/dashboard/client");
  return response.data;
};

export const getFreelancerDashboard = async () => {
  const response = await api.get("/api/v1/dashboard/freelancer");
  return response.data;
};
