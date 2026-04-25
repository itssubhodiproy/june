import { useCallback, useRef, useState, type DragEvent } from "react"

import {
  confirmDocumentUpload,
  createDocumentUploadUrl,
  uploadDocumentToStorage,
  deleteDocument as apiDeleteDocument,
} from "@/api/documents"
import {
  useAddDocumentOptimistic,
  useUpdateDocumentStatus,
  useDeleteDocument,
  useTableDocuments,
  useTableCells,
  useRestoreCells,
  useRestoreDocumentsOrder,
} from "@/stores/table-store"

const PDF_MIME_TYPE = "application/pdf"

function isPdfFile(file: File) {
  const normalizedType = file.type.toLowerCase()
  const normalizedName = file.name.toLowerCase()

  return normalizedType === PDF_MIME_TYPE || normalizedName.endsWith(".pdf")
}

function toFilesArray(files: FileList | File[]) {
  return Array.isArray(files) ? files : Array.from(files)
}

function hasDragFiles(event: DragEvent<HTMLElement>) {
  return Array.from(event.dataTransfer.types).includes("Files")
}

export function useUpload(tableId?: string) {
  const addDocumentOptimistic = useAddDocumentOptimistic()
  const storeDeleteDocument = useDeleteDocument()
  const documents = useTableDocuments()
  const cells = useTableCells()
  const updateDocumentStatus = useUpdateDocumentStatus()
  const storeRestoreCells = useRestoreCells()
  const restoreDocumentsOrder = useRestoreDocumentsOrder()
  const [isUploading, setIsUploading] = useState(false)
  const [lastError, setLastError] = useState<string | null>(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const dragDepthRef = useRef(0)
  const activeUploadsRef = useRef(0)

  function clearLastError() {
    setLastError(null)
  }

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

    activeUploadsRef.current += 1
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
      activeUploadsRef.current = Math.max(0, activeUploadsRef.current - 1)

      if (activeUploadsRef.current === 0) {
        setIsUploading(false)
      }
    }
  }

  // Drag-and-drop handlers
  const dragHandlers = {
    onDragEnter(event: DragEvent<HTMLElement>) {
      if (!hasDragFiles(event)) return
      event.preventDefault()
      dragDepthRef.current += 1
      clearLastError()
      setIsDragActive(true)
    },
    onDragOver(event: DragEvent<HTMLElement>) {
      if (!hasDragFiles(event)) return
      event.preventDefault()
      event.dataTransfer.dropEffect = "copy"
    },
    onDragLeave(event: DragEvent<HTMLElement>) {
      if (!hasDragFiles(event)) return
      event.preventDefault()
      dragDepthRef.current = Math.max(0, dragDepthRef.current - 1)
      if (dragDepthRef.current === 0) {
        setIsDragActive(false)
      }
    },
    onDrop(event: DragEvent<HTMLElement>) {
      if (!hasDragFiles(event)) return
      event.preventDefault()
      dragDepthRef.current = 0
      setIsDragActive(false)
      const { files } = event.dataTransfer
      if (files.length > 0) {
        void startUpload(files)
      }
    },
  }

  const handleDeleteDocument = useCallback(
    async (documentId: string) => {
      if (!tableId) return
      if (!window.confirm("Remove this document from the table and delete all its cells?")) return
      
      const documentSnapshot = documents.byId[documentId]
      if (!documentSnapshot) return

      const cellsSnapshot = { ...cells }
      const orderSnapshot = [...documents.order]
      storeDeleteDocument(documentId)
      
      try {
        await apiDeleteDocument(tableId, documentId)
      } catch {
        addDocumentOptimistic(documentSnapshot)
        storeRestoreCells(cellsSnapshot)
        restoreDocumentsOrder(orderSnapshot)
        setLastError(`Failed to remove document: ${documentSnapshot.file_name}`)
      }
    },
    [
      tableId,
      documents,
      cells,
      storeDeleteDocument,
      addDocumentOptimistic,
      storeRestoreCells,
      restoreDocumentsOrder,
    ]
  )

  return {
    isUploading,
    isDragActive,
    lastError,
    clearLastError,
    startUpload,
    dragHandlers,
    handleDeleteDocument,
  }
}

