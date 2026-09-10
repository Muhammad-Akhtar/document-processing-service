import type { HistoryItem } from '../types/api'

export const HISTORY_STORAGE_KEY = 'docconvert.history.v1'

export function loadHistory(storage: Storage = localStorage): HistoryItem[] {
  try {
    const raw = storage.getItem(HISTORY_STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as HistoryItem[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

export function saveHistory(items: HistoryItem[], storage: Storage = localStorage): void {
  storage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(items.slice(0, 50)))
}

export function upsertHistoryItem(
  items: HistoryItem[],
  item: HistoryItem,
): HistoryItem[] {
  const without = items.filter((x) => x.id !== item.id)
  return [item, ...without].slice(0, 50)
}

export function removeHistoryItem(items: HistoryItem[], id: string): HistoryItem[] {
  return items.filter((x) => x.id !== id)
}
