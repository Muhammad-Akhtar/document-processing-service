import type { HistoryItem } from '../types/api'

type Props = {
  items: HistoryItem[]
  selectedId: string | null
  onSelect: (item: HistoryItem) => void
}

export function HistoryList({ items, selectedId, onSelect }: Props) {
  if (items.length === 0) {
    return <p className="muted history-empty">No recent documents yet.</p>
  }

  return (
    <ul className="history-list">
      {items.map((item) => (
        <li key={item.id}>
          <button
            type="button"
            className={`history-item ${selectedId === item.id ? 'is-selected' : ''}`}
            onClick={() => onSelect(item)}
          >
            <span className="history-name">{item.filename}</span>
            <span className="history-meta">
              {item.status} · {new Date(item.createdAt).toLocaleString()}
            </span>
          </button>
        </li>
      ))}
    </ul>
  )
}
