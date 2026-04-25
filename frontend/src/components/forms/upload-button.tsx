import { useRef } from "react"

import { Upload } from "lucide-react"

import { Button } from "@/components/ui/button"

interface UploadButtonProps {
  disabled?: boolean
  isUploading?: boolean
  onSelectFiles: (files: File[] | FileList) => void
}

export function UploadButton({
  disabled = false,
  isUploading = false,
  onSelectFiles,
}: UploadButtonProps) {
  const inputRef = useRef<HTMLInputElement | null>(null)

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        multiple
        className="sr-only"
        onChange={(event) => {
          const { files } = event.target

          if (files && files.length > 0) {
            const pdfFiles = Array.from(files).filter(
              (file) => file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
            )
            if (pdfFiles.length > 0) {
              onSelectFiles(pdfFiles)
            }
          }

          event.target.value = ""
        }}
      />
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="cursor-pointer"
        disabled={disabled || isUploading}
        onClick={() => inputRef.current?.click()}
      >
        <Upload className="size-4" data-icon="inline-start" />
        {isUploading ? "Uploading…" : "Upload"}
      </Button>
    </>
  )
}
