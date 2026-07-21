import { MODEL_OPTIONS } from "../../lib/models";
import { useChatStore } from "../../store/chatStore";

/** Matches the mockup's model-chip row above the chat — backs plan E2's
 * "Model switching at conversation level" scenario. */
export function ModelPicker() {
  const selected = useChatStore((s) => s.selectedModelProfile);
  const setSelectedModelProfile = useChatStore((s) => s.setSelectedModelProfile);

  return (
    <div className="flex flex-wrap items-center gap-2.5 border-b border-divider py-3.5">
      <span className="mr-1 text-[11px] uppercase tracking-wide text-text-muted">Model</span>
      {MODEL_OPTIONS.map((option) => {
        const isActive = option.profile === selected;
        return (
          <button
            key={option.profile}
            type="button"
            onClick={() => setSelectedModelProfile(option.profile)}
            className={`flex flex-col items-start gap-0.5 rounded-md border px-3.5 py-1.5 ${
              isActive
                ? "border-accent bg-accent-100 text-accent-700"
                : "border-divider bg-transparent text-text-muted"
            }`}
          >
            <span className="font-heading text-[13px] font-semibold">{option.name}</span>
            <span className="text-[10px] text-text-subtle">{option.sub}</span>
          </button>
        );
      })}
    </div>
  );
}
