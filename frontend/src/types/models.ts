export interface Table {
  id: string
  workspace_id: string
  name: string
  document_count: number
  column_count: number
  created_at: string
  updated_at: string
}

export interface TableDocument {
  id: string
  file_name: string
  file_type: string
  file_size: number
  page_count: number | null
  parse_status: "not_ready" | "ready" | "error"
  added_at: string
}

export interface TableColumn {
  id: string
  title: string
  prompt: string
  type: "free_response" | "yes_no" | "date" | "currency" | "verbatim"
  order: number
}

export interface CellSourceReference {
  chunk_id: string
  page: number
  section: string
  quote: string
}

export interface TableCell {
  id: string
  document_id: string
  column_id: string
  status: "empty" | "extracting" | "completed" | "stale" | "error"
  answer: string | null
  reasoning: string | null
  source_references: CellSourceReference[]
}

export interface TableDetail {
  id: string
  workspace_id: string
  name: string
  created_at: string
  updated_at: string
  documents: TableDocument[]
  columns: TableColumn[]
  cells: TableCell[]
}
