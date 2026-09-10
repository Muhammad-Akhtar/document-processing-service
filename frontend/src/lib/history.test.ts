import { beforeEach, describe, expect, it } from 'vitest'
import {
  HISTORY_STORAGE_KEY,
  loadHistory,
  removeHistoryItem,
  saveHistory,
  upsertHistoryItem,
} from './history'
import type { HistoryItem } from '../types/api'

function memoryStorage(): Storage {
  const map = new Map<string, string>()
  return {
    get length() {
      return map.size
    },
    clear: () => map.clear(),
    getItem: (k) => map.get(k) ?? null,
    key: (i) => [...map.keys()][i] ?? null,
    removeItem: (k) => {
      map.delete(k)
    },
    setItem: (k, v) => {
      map.set(k, v)
    },
  }
}

describe('history', () => {
  let storage: Storage

  beforeEach(() => {
    storage = memoryStorage()
  })

  it('round-trips history items', () => {
    const item: HistoryItem = {
      id: '1',
      filename: 'a.html',
      contentType: 'text/html',
      size: 12,
      status: 'uploaded',
      createdAt: '2026-01-01T00:00:00.000Z',
    }
    saveHistory([item], storage)
    expect(storage.getItem(HISTORY_STORAGE_KEY)).toContain('a.html')
    expect(loadHistory(storage)).toEqual([item])
  })

  it('upserts to the front and removes by id', () => {
    const a: HistoryItem = {
      id: 'a',
      filename: 'a.html',
      contentType: 'text/html',
      size: 1,
      status: 'uploaded',
      createdAt: '2026-01-01T00:00:00.000Z',
    }
    const b: HistoryItem = {
      id: 'b',
      filename: 'b.pdf',
      contentType: 'application/pdf',
      size: 2,
      status: 'uploaded',
      createdAt: '2026-01-02T00:00:00.000Z',
    }
    let items = upsertHistoryItem([], a)
    items = upsertHistoryItem(items, b)
    expect(items.map((x) => x.id)).toEqual(['b', 'a'])
    items = upsertHistoryItem(items, { ...a, status: 'converted' })
    expect(items[0]).toMatchObject({ id: 'a', status: 'converted' })
    expect(removeHistoryItem(items, 'a').map((x) => x.id)).toEqual(['b'])
  })
})
