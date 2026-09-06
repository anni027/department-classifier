import type {
  AnswerResponse,
  Department,
  DepartmentDetail,
  SimilarDepartment,
  StartResponse,
  StatusResponse,
} from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(0, "Could not reach the server. Check your connection and try again.");
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.detail ?? `Request failed (${response.status})`);
  }
  return response.json();
}

export function startClassification(): Promise<StartResponse> {
  return request("/classification/start", { method: "POST" });
}

export function submitAnswer(sessionId: string, questionId: string, response: number): Promise<AnswerResponse> {
  return request("/classification/answer", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, question_id: questionId, response }),
  });
}

export function getStatus(sessionId: string): Promise<StatusResponse> {
  return request(`/classification/status/${sessionId}`);
}

export function listDepartments(): Promise<Department[]> {
  return request("/departments");
}

export function getDepartment(id: string): Promise<DepartmentDetail> {
  return request(`/departments/${id}`);
}

export function getSimilarDepartments(id: string): Promise<SimilarDepartment[]> {
  return request(`/departments/${id}/similar`);
}
