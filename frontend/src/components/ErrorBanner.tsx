type Props = {
  message: string | null
  onDismiss: () => void
}

export function ErrorBanner({ message, onDismiss }: Props) {
  if (!message) return null
  return (
    <div className="banner banner-error" role="alert">
      <p>{message}</p>
      <button type="button" className="banner-dismiss" onClick={onDismiss}>
        Dismiss
      </button>
    </div>
  )
}
