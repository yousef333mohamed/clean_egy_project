export interface ApiErrorShape {
  status: number;
  message: string;
  code?: string;
  requestId?: string;
  details?: unknown;
}

export class ApiError extends Error implements ApiErrorShape {
  status: number;
  code?: string;
  requestId?: string;
  details?: unknown;

  constructor(error: ApiErrorShape) {
    super(error.message);
    this.name = "ApiError";
    this.status = error.status;
    this.code = error.code;
    this.requestId = error.requestId;
    this.details = error.details;
  }
}

export function userErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError))
    return "Something went wrong. Try again or check the backend connection.";
  const messages: Record<number, string> = {
    400: "The request was not accepted. Review the entered values.",
    403: "This feature is disabled or unavailable for this environment.",
    404: "The requested resource was not found.",
    409: "The resource conflicts with an existing version.",
    422: "Validation failed. Review the highlighted fields.",
    500: "The backend could not complete the request.",
    503: "A required backend service is temporarily unavailable.",
  };
  return messages[error.status] ?? error.message;
}
