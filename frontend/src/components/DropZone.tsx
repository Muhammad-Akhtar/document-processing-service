type Props = {
  disabled?: boolean
  onFile: (file: File) => void
}

export function DropZone({ disabled, onFile }: Props) {
  function takeFiles(list: FileList | null) {
    const file = list?.[0]
    if (file) onFile(file)
  }

  return (
    <label
      className={`dropzone ${disabled ? 'is-disabled' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
      }}
      onDrop={(e) => {
        e.preventDefault()
        if (!disabled) takeFiles(e.dataTransfer.files)
      }}
    >
      <input
        type="file"
        accept=".html,.htm,.pdf,text/html,application/pdf"
        disabled={disabled}
        onChange={(e) => takeFiles(e.target.files)}
      />
      <span className="dropzone-title">Drop HTML or PDF here</span>
      <span className="dropzone-sub">or click to browse · max 10 MB</span>
    </label>
  )
}
