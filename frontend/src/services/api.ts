import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const optimizeRoute = async (payload: any) => {
  const response = await api.post("/optimize_route", payload);
  return response.data;
};
