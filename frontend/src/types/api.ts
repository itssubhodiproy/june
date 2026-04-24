export interface DocumentUploadUrlRequest {
  file_name: string
  file_type: string
  file_size: number
  table_id: string
}

export interface DocumentUploadUrlResponse {
  doc_id: string
  upload_url: string
  file_key: string
}

export interface DocumentConfirmResponse {
  doc_id: string
  parse_status: "not_ready" | "queued" | "ready" | "error"
}
