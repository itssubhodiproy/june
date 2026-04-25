import type {
  DocumentConfirmResponse,
  DocumentUploadUrlRequest,
  DocumentUploadUrlResponse,
} from "@/types/api"

import { fetchWithAuth } from "./client"

export async function createDocumentUploadUrl(
  data: DocumentUploadUrlRequest
): Promise<DocumentUploadUrlResponse> {
  return fetchWithAuth<DocumentUploadUrlResponse>("/api/documents/upload-url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export async function uploadDocumentToStorage(uploadUrl: string, file: File): Promise<void> {
  const response = await fetch(uploadUrl, {
    method: "PUT",
    headers: {
      "Content-Type": file.type || "application/pdf",
    },
    body: file,
  })

  if (!response.ok) {
    throw new Error("Failed to upload file")
  }
}

export async function confirmDocumentUpload(docId: string): Promise<DocumentConfirmResponse> {
  return fetchWithAuth<DocumentConfirmResponse>(`/api/documents/${docId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  })
}

export async function deleteDocument(tableId: string, docId: string): Promise<void> {
  return fetchWithAuth<void>(`/api/tables/${tableId}/documents/${docId}`, {
    method: "DELETE",
  })
}
