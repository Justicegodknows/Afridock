export type ModelOption = {
  profile: string;
  name: string;
  sub: string;
};

/**
 * Mirrors apps/api/src/afridock_api/inference/profiles.yaml — kept as a
 * small static list here rather than fetched, since the plan's model set
 * changes rarely and this avoids a chat-blocking request before the picker
 * can render. Keep in sync with profiles.yaml manually until there's an
 * endpoint worth adding just for this.
 */
export const MODEL_OPTIONS: ModelOption[] = [
  { profile: "llama-3.2-1b-instruct", name: "Llama 3.2 1B", sub: "Default · Self-hosted Ollama" },
  { profile: "llama-3.1-8b-nim", name: "Llama 3.1 8B", sub: "Self-hosted NVIDIA NIM" },
  { profile: "llama-3.3-70b-nvidia", name: "Llama 3.3 70B", sub: "NVIDIA hosted" },
  { profile: "llama-3.1-8b-instruct", name: "Llama 3.1 8B", sub: "Hugging Face" },
  { profile: "llama-3.1-70b-instruct", name: "Llama 3.1 70B", sub: "Hugging Face" },
  { profile: "mixtral-8x7b-instruct", name: "Mixtral 8x7B", sub: "Self-hosted vLLM" },
  { profile: "claude-fallback", name: "Claude", sub: "Commercial fallback" },
  { profile: "gpt-fallback", name: "GPT-4o", sub: "Commercial fallback" },
];
