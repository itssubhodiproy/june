import { useState } from "react"

import {
  confirmDocumentUpload,
  createDocumentUploadUrl,
  uploadDocumentToStorage,
} from "@/api/documents"
import { useAddDocumentOptimistic, useUpdateDocumentStatus } from "@/stores/table-store"

const PDF_MIME_TYPE = "application/pdf"

function isPdfFile(file: File) {
  const normalizedType = file.type.toLowerCase()
  const normalizedName = file.name.toLowerCase()

  return normalizedType === PDF_MIME_TYPE || normalizedName.endsWith(".pdf")
}

function toFilesArray(files: FileList | File[]) {
  return Array.isArray(files) ? files : Array.from(files)
}

export function useUpload(tableId?: string) {
  const addDocumentOptimistic = useAddDocumentOptimistic()
  const updateDocumentStatus = useUpdateDocumentStatus()
  const [isUploading, setIsUploading] = useState(false)
  const [lastError, setLastError] = useState<string | null>(null)

  async function startUpload(files: FileList | File[]) {
    if (!tableId) {
      setLastError("Missing table id")
      return
    }

    const resolvedTableId = tableId

    const selectedFiles = toFilesArray(files)
    const validFiles = selectedFiles.filter((file) => file.size > 0 && isPdfFile(file))

    if (validFiles.length === 0) {
      setLastError("Only PDF files can be uploaded.")
      return
    }

    setIsUploading(true)
    setLastError(null)

    async function uploadSingleFile(file: File) {
      let documentId: string | null = null

      try {
        const uploadData = await createDocumentUploadUrl({
          file_name: file.name,
          file_type: file.type || PDF_MIME_TYPE,
          file_size: file.size,
          table_id: resolvedTableId,
        })
        documentId = uploadData.doc_id

        addDocumentOptimistic({
          id: uploadData.doc_id,
          file_name: file.name,
          file_type: file.type || PDF_MIME_TYPE,
          file_size: file.size,
          page_count: null,
          parse_status: "not_ready",
          added_at: new Date().toISOString(),
        })

        await uploadDocumentToStorage(uploadData.upload_url, file)

        const confirmData = await confirmDocumentUpload(uploadData.doc_id)
        updateDocumentStatus(uploadData.doc_id, confirmData.parse_status)
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to upload document"

        setLastError(`Failed to upload ${file.name}: ${message}`)

        if (error instanceof Error) {
          console.error(error)
        }

        if (documentId) {
          updateDocumentStatus(documentId, "error")
        }
      }
    }

    const MAX_CONCURRENT = 5
    const executing = new Set<Promise<void>>()

    try {
      for (const file of validFiles) {
        const task = uploadSingleFile(file).finally(() => executing.delete(task))
        executing.add(task)

        if (executing.size >= MAX_CONCURRENT) {
          await Promise.race(executing)
        }
      }

      await Promise.all(executing)
    } finally {
      setIsUploading(false)
    }
  }

  return {
    isUploading,
    lastError,
    clearLastError: () => setLastError(null),
    startUpload,
  }
}
