export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024

const HTML_TYPES = new Set(['text/html', 'application/xhtml+xml'])
const PDF_TYPES = new Set(['application/pdf'])

export type SourceKind = 'html' | 'pdf' | 'unknown'

export function extensionOf(filename: string): string {
  const i = filename.lastIndexOf('.')
  return i >= 0 ? filename.slice(i).toLowerCase() : ''
}

export function detectSourceKind(filename: string, contentType?: string): SourceKind {
  const ext = extensionOf(filename)
  const type = (contentType || '').split(';')[0].trim().toLowerCase()
  if (ext === '.html' || ext === '.htm' || HTML_TYPES.has(type)) return 'html'
  if (ext === '.pdf' || PDF_TYPES.has(type)) return 'pdf'
  return 'unknown'
}

export function targetFormatFor(kind: SourceKind): 'pdf' | 'html' | null {
  if (kind === 'html') return 'pdf'
  if (kind === 'pdf') return 'html'
  return null
}

export function isAllowedUpload(filename: string, size: number): { ok: true } | { ok: false; reason: string } {
  if (size <= 0) return { ok: false, reason: 'Empty files are not allowed' }
  if (size > MAX_UPLOAD_BYTES) {
    return { ok: false, reason: `File exceeds ${MAX_UPLOAD_BYTES} bytes` }
  }
  const kind = detectSourceKind(filename)
  if (kind === 'unknown') {
    return { ok: false, reason: 'Only .html, .htm, and .pdf files are accepted' }
  }
  return { ok: true }
}
