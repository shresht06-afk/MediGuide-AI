const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const networkErrorMessage = "We couldn't reach MediGuide right now. Please try again in a moment.";
const requestErrorMessage = "MediGuide couldn't complete that request. Please try again in a moment.";

export type Conversation = { id: string; title: string; created_at: string; updated_at: string; status: string };
export type MessageResponse = { message_id: string; content: string; topic: string; safety: string; response_time: number };
export type FeedbackResponse = { status: "recorded" };

export class ApiError extends Error { constructor(message: string, public status?: number) { super(message); this.name = "ApiError"; } }
const responseError = () => new ApiError(requestErrorMessage);

export const getUserFacingError = (error: unknown) => error instanceof ApiError ? error.message : requestErrorMessage;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(`${apiUrl}${path}`, { ...init, headers: { "Content-Type": "application/json", ...init?.headers } }); }
  catch { throw new ApiError(networkErrorMessage); }
  const body = await response.json().catch(() => null) as { detail?: string } | T | null;
  if (!response.ok) { throw new ApiError(response.status === 503 ? "MediGuide is temporarily unavailable. Please try again in a moment." : requestErrorMessage, response.status); }
  if (!body || typeof body !== "object") throw responseError();
  return body as T;
}

export const createConversation = async () => {
  const conversation = await request<Conversation>("/api/conversations", { method: "POST" });
  if (!conversation.id) throw responseError();
  return conversation;
};
export const sendMessage = async (conversationId: string, content: string) => {
  const response = await request<MessageResponse>(`/api/conversations/${conversationId}/messages`, { method: "POST", body: JSON.stringify({ content }) });
  if (!response.message_id || !response.content || !response.safety) throw responseError();
  return response;
};
export const submitFeedback = (messageId: string, rating: 0 | 1, comment?: string) => request<FeedbackResponse>(`/api/messages/${messageId}/feedback`, { method: "POST", body: JSON.stringify({ rating, comment }) });
