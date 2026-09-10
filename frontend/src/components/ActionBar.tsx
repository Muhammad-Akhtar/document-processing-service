type Props = {
  canConvert: boolean
  convertLabel: string
  converting: boolean
  canDownload: boolean
  canDelete: boolean
  onConvert: () => void
  onDownload: () => void
  onDelete: () => void
}

export function ActionBar({
  canConvert,
  convertLabel,
  converting,
  canDownload,
  canDelete,
  onConvert,
  onDownload,
  onDelete,
}: Props) {
  return (
    <div className="actions" role="toolbar" aria-label="Document actions">
      <button type="button" className="btn primary" disabled={!canConvert || converting} onClick={onConvert}>
        {converting ? 'Converting…' : convertLabel}
      </button>
      <button type="button" className="btn" disabled={!canDownload} onClick={onDownload}>
        Download
      </button>
      <button type="button" className="btn danger" disabled={!canDelete} onClick={onDelete}>
        Delete
      </button>
    </div>
  )
}
