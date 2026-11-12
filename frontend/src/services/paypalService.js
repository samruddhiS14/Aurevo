import api from "./api";

// Create a PayPal order for a milestone
export const createMilestoneOrder = async (milestoneId) => {
  const response = await api.post(
    `/api/payments/milestones/${milestoneId}/create-order`
  );

  return response.data;
};

// Authorize the order after the client approves it on PayPal
export const authorizePayPalOrder = async (orderId) => {
  const response = await api.post(
    `/api/payments/orders/${encodeURIComponent(orderId)}/authorize`
  );

  return response.data;
};

export const captureMilestonePayment = async (milestoneId) => {
  const response = await api.post(`/api/payments/milestones/${milestoneId}/capture`);
  return response.data;
};
