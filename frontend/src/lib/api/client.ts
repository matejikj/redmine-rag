import type {
  AskRequest,
  AskResponse,
  HealthResponse,
  SyncJobResponse,
  SyncJobListResponse,
  SyncRequest,
  SyncResponse
} from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly actionableMessage: string;

  constructor(status: number, message: string, actionableMessage: string) {
    super(message);
    this.status = status;
    this.actionableMessage = actionableMessage;
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  signal?: AbortSignal;
}

async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(path, {
    method: options.method ?? "GET",
    signal: options.signal,
    headers: {
      "content-type": "application/json"
    },
    body: options.body === undefined ? undefined : JSON.stringify(options.body)
  });

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // keep default detail
    }

    throw new ApiError(response.status, detail, toActionableMessage(response.status, detail));
  }

  return (await response.json()) as T;
}

function toActionableMessage(status: number, detail: string): string {
  if (status >= 500) {
    return "Server-side failure. Verify /healthz and retry once the backend is healthy.";
  }
  if (status === 404) {
    return "Requested resource was not found. Refresh data or check selected filters.";
  }
  if (status === 422) {
    return "Invalid input. Adjust required fields and submit again.";
  }
  return `Request failed: ${detail}`;
}

export const apiClient = {
  getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    return requestJson<HealthResponse>("/healthz", { signal });
  },
  runAsk(payload: AskRequest, signal?: AbortSignal): Promise<AskResponse> {
    return requestJson<AskResponse>("/v1/ask", {
      method: "POST",
      body: payload,
      signal
    });
  },
  triggerSync(payload: SyncRequest): Promise<SyncResponse> {
    return requestJson<SyncResponse>("/v1/sync/redmine", {
      method: "POST",
      body: payload
    });
  },
  listSyncJobs(params: { limit?: number; status?: string } = {}): Promise<SyncJobListResponse> {
    const search = new URLSearchParams();
    search.set("limit", String(params.limit ?? 20));
    if (params.status) {
      search.set("status", params.status);
    }
    return requestJson<SyncJobListResponse>(`/v1/sync/jobs?${search.toString()}`);
  },
  getSyncJob(jobId: string): Promise<SyncJobResponse> {
    return requestJson<SyncJobResponse>(`/v1/sync/jobs/${jobId}`);
  }
};
