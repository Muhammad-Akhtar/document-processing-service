import { describe, expect, it } from 'vitest'
import {
  detectSourceKind,
  isAllowedUpload,
  MAX_UPLOAD_BYTES,
  targetFormatFor,
} from '../lib/formats'

describe('formats', () => {
  it('detects html and pdf sources', () => {
    expect(detectSourceKind('a.html')).toBe('html')
    expect(detectSourceKind('a.HTM')).toBe('html')
    expect(detectSourceKind('a.pdf')).toBe('pdf')
    expect(detectSourceKind('a.exe')).toBe('unknown')
  })

  it('maps conversion targets', () => {
    expect(targetFormatFor('html')).toBe('pdf')
    expect(targetFormatFor('pdf')).toBe('html')
    expect(targetFormatFor('unknown')).toBeNull()
  })

  it('rejects empty, oversized, and bad extensions', () => {
    expect(isAllowedUpload('a.html', 0).ok).toBe(false)
    expect(isAllowedUpload('a.html', MAX_UPLOAD_BYTES + 1).ok).toBe(false)
    expect(isAllowedUpload('a.exe', 10).ok).toBe(false)
    expect(isAllowedUpload('a.html', 10)).toEqual({ ok: true })
  })
})
