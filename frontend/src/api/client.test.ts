import { describe, expect, it } from 'vitest'
import { apiUrl } from './client'

describe('api client', () => {
  it('builds relative api paths', () => {
    expect(apiUrl('/api/v1/documents')).toBe('/api/v1/documents')
    expect(apiUrl('api/v1/documents')).toBe('/api/v1/documents')
  })
})
