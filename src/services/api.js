// src/services/api.js
import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";


const api = axios.create({
  baseURL: BASE_URL,
});

export const getDashboardData = async () => {
  try {
    // Check this endpoint! 
    const response = await api.get('/api/data'); 
    return response.data;
  } catch (error) {
    console.error("API Call Failed:", error);
    // This is likely where the "Network Error" message is being generated/displayed.
    throw new Error("Network Error"); 
  }
};