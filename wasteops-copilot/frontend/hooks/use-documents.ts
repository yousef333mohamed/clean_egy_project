"use client";
import { useQuery } from "@tanstack/react-query";
import { getDocuments } from "@/lib/api/documents";
export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: ({ signal }) => getDocuments(signal),
    staleTime: 120_000,
  });
}
