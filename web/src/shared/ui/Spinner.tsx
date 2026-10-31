export function Spinner({ label = "Завантаження" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center">
      <span className="size-4 animate-spin rounded-full border border-current border-t-transparent" aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </span>
  );
}
