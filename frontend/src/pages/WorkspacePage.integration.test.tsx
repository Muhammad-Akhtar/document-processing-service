import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { WorkspacePage } from './WorkspacePage'
import { HISTORY_STORAGE_KEY } from '../lib/history'

const uploadDocument = vi.fn()
const convertDocument = vi.fn()
const deleteDocument = vi.fn()
const previewUrl = vi.fn((id: string) => `/api/v1/documents/${id}/preview`)
const downloadUrl = vi.fn((id: string) => `/api/v1/documents/${id}/download`)

vi.mock('../api/documents', () => ({
  uploadDocument: (...args: unknown[]) => uploadDocument(...args),
  convertDocument: (...args: unknown[]) => convertDocument(...args),
  deleteDocument: (...args: unknown[]) => deleteDocument(...args),
  previewUrl: (id: string) => previewUrl(id),
  downloadUrl: (id: string) => downloadUrl(id),
}))

describe('WorkspacePage integration', () => {
  beforeEach(() => {
    localStorage.clear()
    uploadDocument.mockReset()
    convertDocument.mockReset()
    deleteDocument.mockReset()
    uploadDocument.mockResolvedValue({
      document_id: 'doc-1',
      filename: 'sample.html',
      content_type: 'text/html',
      size: 42,
    })
    convertDocument.mockResolvedValue({
      source_document_id: 'doc-1',
      output_document_id: 'out-1',
      target_format: 'pdf',
      filename: 'sample.pdf',
      content_type: 'application/pdf',
      size: 100,
      page_count: 1,
      warnings: [],
      download_url: '/api/v1/documents/out-1/download',
    })
    deleteDocument.mockResolvedValue(undefined)
  })

  afterEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders shell and empty preview state', () => {
    render(<WorkspacePage />)
    expect(screen.getByRole('heading', { name: 'DocConvert' })).toBeInTheDocument()
    expect(screen.getByText(/Drop HTML or PDF here/i)).toBeInTheDocument()
    expect(screen.getByText(/Select or upload a document to preview/i)).toBeInTheDocument()
    expect(screen.getByText(/No recent documents yet/i)).toBeInTheDocument()
  })

  it('uploads a file, converts, and records history', async () => {
    const user = userEvent.setup()
    render(<WorkspacePage />)

    const file = new File(['<html><body>hi</body></html>'], 'sample.html', {
      type: 'text/html',
    })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, file)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'sample.html' })).toBeInTheDocument()
    })
    expect(uploadDocument).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: /Convert to PDF/i })).toBeEnabled()

    await user.click(screen.getByRole('button', { name: /Convert to PDF/i }))

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'sample.pdf' })).toBeInTheDocument()
    })
    expect(convertDocument).toHaveBeenCalledWith('doc-1', 'pdf')

    const stored = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]') as Array<{
      id: string
      status: string
    }>
    expect(stored.some((item) => item.id === 'out-1' && item.status === 'converted')).toBe(true)
  })

  it('shows client-side validation errors for disallowed files', async () => {
    const user = userEvent.setup()
    render(<WorkspacePage />)

    const file = new File(['MZ'], 'virus.exe', { type: 'application/octet-stream' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    // Bypass browser accept filtering used by userEvent.upload
    Object.defineProperty(input, 'files', {
      configurable: true,
      value: {
        0: file,
        length: 1,
        item: (i: number) => (i === 0 ? file : null),
      },
    })
    await user.click(input)
    input.dispatchEvent(new Event('change', { bubbles: true }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/Only \.html/i)
    expect(uploadDocument).not.toHaveBeenCalled()
  })

  it('deletes the selected document after confirm', async () => {
    const user = userEvent.setup()
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(<WorkspacePage />)
    const file = new File(['<html></html>'], 'sample.html', { type: 'text/html' })
    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    await user.upload(input, file)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Delete/i })).toBeEnabled()
    })
    await user.click(screen.getByRole('button', { name: /Delete/i }))

    await waitFor(() => {
      expect(screen.getByText(/Select or upload a document to preview/i)).toBeInTheDocument()
    })
    expect(deleteDocument).toHaveBeenCalledWith('doc-1')
  })
})
