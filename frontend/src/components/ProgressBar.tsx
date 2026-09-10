type Props = {
  value: number
  label?: string
}

export function ProgressBar({ value, label }: Props) {
  const clamped = Math.max(0, Math.min(1, value))
  return (
    <div className="progress" aria-label={label ?? 'Progress'}>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${clamped * 100}%` }} />
      </div>
      <span className="progress-label">{Math.round(clamped * 100)}%</span>
    </div>
  )
}
