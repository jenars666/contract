import axios from "axios";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const api = axios.create({ baseURL: apiBaseUrl });

function mapError(error) {
  if (error?.response?.data?.detail) return error.response.data.detail;
  if (error?.response?.data?.error) return error.response.data.error;
  if (error?.message) return error.message;
  return "Unexpected API error";
}

export async function analyzeContract(code, filename = "contract.sol") {
  try {
    const response = await api.post("/api/analyze", { code, filename });
    return response.data;
  } catch (error) {
    throw new Error(mapError(error));
  }
}

export async function generatePatch(code, vulnerabilities) {
  try {
    const response = await api.post("/api/patch", { code, vulnerabilities });
    return response.data;
  } catch (error) {
    throw new Error(mapError(error));
  }
}

export async function checkHealth() {
  try {
    const response = await api.get("/api/health");
    return response.data;
  } catch (error) {
    throw new Error(mapError(error));
  }
}
export async function pushToGithub(filename, code, commitMessage) {
  try {
    const response = await api.post("/api/push", {
      filename,
      code,
      commit_message: commitMessage,
    });
    return response.data;
  } catch (error) {
    throw new Error(mapError(error));
  }
}
