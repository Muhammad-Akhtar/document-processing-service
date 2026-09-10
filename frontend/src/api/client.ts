import type { ApiErrorBody } from '../types/api'

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? ''

export class ApiError extends Error {
  readonly code: string
  readonly status: number
  readonly details: unknown

  constructor(status: number, body: ApiErrorBody) {
    super(body.message || `Request failed (${status})`)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code || 'api_error'
    this.details = body.details
  }
}

export function apiUrl(path: string): string {
  if (path.startsWith('http')) return path
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
}

export async function parseError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as ApiErrorBody
    return new ApiError(response.status, body)
  } catch {
    return new ApiError(response.status, {
      code: 'http_error',
      message: response.statusText || `HTTP ${response.status}`,
    })
  }
}

export async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), init)
  if (!response.ok) throw await parseError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
