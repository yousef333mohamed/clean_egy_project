"use client";
import { useQuery } from "@tanstack/react-query";
import { getOperationalOverview } from "@/lib/api/analytics";
export function useOperationalOverview() {
  return useQuery({
    queryKey: ["operational-overview"],
    queryFn: ({ signal }) => getOperationalOverview(signal),
    staleTime: 120_000,
  });
}
