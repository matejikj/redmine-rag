import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "./client";
import type { AskRequest, ExtractRequest, OpsBackupRequest, SyncRequest } from "./types";

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

export function useMetricsSummaryQuery(params: {
  projectIds: number[];
  fromDate: string | null;
  toDate: string | null;
}) {
  return useQuery({
    queryKey: ["metrics-summary", params.projectIds, params.fromDate, params.toDate],
    queryFn: () => apiClient.getMetricsSummary(params),
    staleTime: 10_000,
    refetchInterval: 60_000
  });
}

export function useEvalArtifactsQuery() {
  return useQuery({
    queryKey: ["eval-artifacts-latest"],
    queryFn: () => apiClient.getEvalArtifacts(),
    staleTime: 20_000,
    refetchInterval: 90_000
  });
}

export function useOpsEnvironmentQuery() {
  return useQuery({
    queryKey: ["ops-environment"],
    queryFn: () => apiClient.getOpsEnvironment(),
    staleTime: 60_000,
    refetchInterval: 120_000
  });
}

export function useOpsRunsQuery() {
  return useQuery({
    queryKey: ["ops-runs"],
    queryFn: () => apiClient.listOpsRuns({ limit: 20 }),
    staleTime: 3_000,
    refetchInterval: 5_000
  });
}

export function useSyncJobQuery(jobId: string | null) {
  return useQuery({
    queryKey: ["sync-job", jobId],
    queryFn: () => apiClient.getSyncJob(jobId as string),
    enabled: Boolean(jobId),
    staleTime: 1_000,
    refetchInterval: 3_000
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

export function useExtractMutation() {
  return useMutation({
    mutationFn: (payload: ExtractRequest) => apiClient.runExtraction(payload)
  });
}

export function useOpsBackupMutation() {
  return useMutation({
    mutationFn: (payload: OpsBackupRequest) => apiClient.runOpsBackup(payload)
  });
}

export function useOpsMaintenanceMutation() {
  return useMutation({
    mutationFn: () => apiClient.runOpsMaintenance()
  });
}
