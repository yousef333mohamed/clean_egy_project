"use client";
import { useQuery } from "@tanstack/react-query";
import { getIngestionFiles } from "@/lib/api/ingestion";
import { getDocumentFiles } from "@/lib/api/documents";
export function useIngestionFiles() {
  return useQuery({
    queryKey: ["ingestion-files"],
    queryFn: ({ signal }) => getIngestionFiles(signal),
  });
}
export function useDocumentFiles() {
  return useQuery({
    queryKey: ["document-files"],
    queryFn: ({ signal }) => getDocumentFiles(signal),
  });
}
