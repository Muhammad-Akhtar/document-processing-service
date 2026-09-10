import { ApiError, apiUrl, parseError } from './client'
import type { ConversionResponse, DocumentMeta, UploadResponse } from '../types/api'

export async function uploadDocument(
  file: File,
  onProgress?: (ratio: number) => void,
): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)

  if (!onProgress) {
    const response = await fetch(apiUrl('/api/v1/documents'), {
      method: 'POST',
      body: form,
    })
    if (!response.ok) throw await parseError(response)
    return (await response.json()) as UploadResponse
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', apiUrl('/api/v1/documents'))
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(event.loaded / event.total)
    }
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as UploadResponse)
        return
      }
      try {
        const body = JSON.parse(xhr.responseText) as {
          code: string
          message: string
          details?: unknown
        }
        reject(new ApiError(xhr.status, body))
      } catch {
        reject(new Error(xhr.statusText || `HTTP ${xhr.status}`))
      }
    }
    xhr.onerror = () => reject(new Error('Network error during upload'))
    xhr.send(form)
  })
}

export function getDocument(documentId: string): Promise<DocumentMeta> {
  return fetch(apiUrl(`/api/v1/documents/${documentId}`)).then(async (response) => {
    if (!response.ok) throw await parseError(response)
    return (await response.json()) as DocumentMeta
  })
}

export async function deleteDocument(documentId: string): Promise<void> {
  const response = await fetch(apiUrl(`/api/v1/documents/${documentId}`), {
    method: 'DELETE',
  })
  if (!response.ok) throw await parseError(response)
}

export function previewUrl(documentId: string): string {
  return apiUrl(`/api/v1/documents/${documentId}/preview`)
}

export function downloadUrl(documentId: string): string {
  return apiUrl(`/api/v1/documents/${documentId}/download`)
}

export async function convertDocument(
  sourceDocumentId: string,
  targetFormat: string,
): Promise<ConversionResponse> {
  const response = await fetch(apiUrl('/api/v1/conversions'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_document_id: sourceDocumentId,
      target_format: targetFormat,
    }),
  })
  if (!response.ok) throw await parseError(response)
  return (await response.json()) as ConversionResponse
}
