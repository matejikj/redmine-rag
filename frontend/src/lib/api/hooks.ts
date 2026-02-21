import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "./client";
import type { AskRequest, SyncRequest } from "./types";

export function useHealthQuery() {
  return useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => apiClient.getHealth(signal),
    staleTime: 15_000,
    refetchInterval: 30_000
  });
}

export function useSyncJobsQuery(status: string | null) {
  return useQuery({
    queryKey: ["sync-jobs", status],
    queryFn: () => apiClient.listSyncJobs({ limit: 20, status: status ?? undefined }),
    staleTime: 2_000,
    refetchInterval: 5_000
  });
}

export function useTriggerSyncMutation() {
  return useMutation({
    mutationFn: (payload: SyncRequest) => apiClient.triggerSync(payload)
  });
}

export function useAskMutation() {
  return useMutation({
    mutationFn: (payload: AskRequest) => apiClient.runAsk(payload)
  });
}
