export type UploadResponse = {
  document_id: string
  filename: string
  content_type: string
  size: number
}

export type DocumentMeta = {
  id: string
  original_filename: string
  content_type: string
  size: number
  stored_path: string
  created_at: string
  page_count?: number | null
  title?: string | null
}

export type ConversionResponse = {
  source_document_id: string
  output_document_id: string
  target_format: string
  filename: string
  content_type: string
  size: number
  page_count?: number | null
  title?: string | null
  warnings: string[]
  download_url: string
}

export type ApiErrorBody = {
  code: string
  message: string
  details?: unknown
}

export type HistoryItem = {
  id: string
  filename: string
  contentType: string
  size: number
  status: 'uploaded' | 'converted' | 'failed'
  createdAt: string
  sourceDocumentId?: string
  targetFormat?: string
}
