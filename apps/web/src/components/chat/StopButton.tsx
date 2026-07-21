type StopButtonProps = {
  isResponding: boolean;
  onStop: () => void;
};

export function StopButton({ isResponding, onStop }: StopButtonProps) {
  if (!isResponding) return null;

  return (
    <button
      type="button"
      onClick={onStop}
      className="rounded-md border border-divider px-3 py-1 text-xs text-text-muted hover:bg-hover-overlay"
    >
      Stop generating
    </button>
  );
}
