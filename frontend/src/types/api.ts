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

export interface ColumnCreateRequest {
  title: string
  prompt: string
  type: "free_response" | "yes_no" | "date" | "currency" | "verbatim"
}

export interface ColumnCreateResponse {
  id: string
  table_id: string
  title: string
  prompt: string
  type: "free_response" | "yes_no" | "date" | "currency" | "verbatim"
  order: number
  created_at: string
}

export interface ColumnUpdateRequest {
  title?: string
  prompt?: string
  type?: "free_response" | "yes_no" | "date" | "currency" | "verbatim"
}

export interface ColumnUpdateResponse {
  id: string
  title: string
  prompt: string
  type: "free_response" | "yes_no" | "date" | "currency" | "verbatim"
  order: number
  updated_at: string
}
