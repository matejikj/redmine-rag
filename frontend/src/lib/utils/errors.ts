import { ApiError } from "../api/client";

export function toUserMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.actionableMessage;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error. Retry the action or verify API availability.";
}
