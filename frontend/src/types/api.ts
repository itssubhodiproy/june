import type { ColumnType, ParseStatus } from "./models"

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
  parse_status: ParseStatus
}

export interface ColumnCreateRequest {
  title: string
  prompt: string
  type: ColumnType
}

export interface ColumnCreateResponse {
  id: string
  table_id: string
  title: string
  prompt: string
  type: ColumnType
  order: number
  created_at: string
}

export interface ColumnUpdateRequest {
  title?: string
  prompt?: string
  type?: ColumnType
}

export interface ColumnUpdateResponse {
  id: string
  title: string
  prompt: string
  type: ColumnType
  order: number
  updated_at: string
}
