"use client"

import { useRef, useState } from "react"
import { Camera, Loader2, X } from "lucide-react"
import { type Photo } from "@/lib/findings"

const MAX_PHOTOS = 5

interface PhotoUploadProps {
  inspectionId: string
  findingId: string
  photos: Photo[]
  onPhotosChange: (photos: Photo[]) => void
}

export function PhotoUpload({
  inspectionId,
  findingId,
  photos,
  onPhotosChange,
}: PhotoUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)

    try {
      const contentType = file.type || "image/jpeg"

      // 1. Get presigned upload URL
      const urlRes = await fetch(
        `/api/inspections/${inspectionId}/findings/${findingId}/photos`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content_type: contentType }),
        },
      )
      if (!urlRes.ok) throw new Error("Failed to get upload URL.")
      const { upload_url, view_url, key } = (await urlRes.json()) as {
        upload_url: string
        view_url: string
        key: string
      }

      // 2. PUT directly to S3 (file never touches Next.js)
      const s3Res = await fetch(upload_url, {
        method: "PUT",
        headers: { "Content-Type": contentType },
        body: file,
      })
      if (!s3Res.ok) throw new Error("Upload to storage failed.")

      // 3. Save photo record on the finding
      const addRes = await fetch(
        `/api/inspections/${inspectionId}/findings/${findingId}/photos/add`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key, view_url }),
        },
      )
      if (!addRes.ok) throw new Error("Failed to save photo record.")

      onPhotosChange([...photos, { key, view_url }])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.")
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  async function handleRemove(key: string) {
    setError(null)
    try {
      const res = await fetch(
        `/api/inspections/${inspectionId}/findings/${findingId}/photos/remove`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ key }),
        },
      )
      if (!res.ok) throw new Error("Failed to remove photo.")
      onPhotosChange(photos.filter((p) => p.key !== key))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove photo.")
    }
  }

  return (
    <div className="space-y-2">
      <span className="text-sm font-medium">Photos</span>
      <div className="flex flex-wrap gap-2">
        {photos.map((photo) => (
          <div key={photo.key} className="relative size-12 shrink-0">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={photo.view_url}
              alt="Finding photo"
              className="size-full rounded-md border border-border object-cover"
            />
            <button
              type="button"
              onClick={() => handleRemove(photo.key)}
              aria-label="Remove photo"
              className="absolute -right-1 -top-1 flex size-4 items-center justify-center rounded-full bg-destructive text-destructive-foreground shadow-sm"
            >
              <X className="size-2.5" />
            </button>
          </div>
        ))}

        {uploading && (
          <div className="flex size-12 shrink-0 items-center justify-center rounded-md border border-border bg-muted">
            <Loader2 className="size-4 animate-spin text-muted-foreground" />
          </div>
        )}

        {!uploading && photos.length < MAX_PHOTOS && (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            aria-label="Add photo"
            className="flex size-12 shrink-0 items-center justify-center rounded-md border border-dashed border-border text-muted-foreground transition-colors hover:border-primary hover:text-primary"
          >
            <Camera className="size-5" />
          </button>
        )}
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileSelect}
      />
    </div>
  )
}
