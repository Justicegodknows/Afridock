import { useEffect, useRef } from "react";

const SCROLL_LOCK_THRESHOLD_PX = 80;

/**
 * Auto-scrolls a container to the bottom as `dependency` changes, unless the
 * user has manually scrolled away from the bottom — ports Dify's scroll-lock
 * pattern (web/app/components/base/chat/chat/use-chat-layout.ts) without its
 * ResizeObserver-driven footer tracking, which Afridock doesn't need yet.
 */
export function useAutoScroll<T extends HTMLElement>(dependency: unknown) {
  const containerRef = useRef<T | null>(null);
  const userScrolledUpRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
      userScrolledUpRef.current = distanceToBottom > SCROLL_LOCK_THRESHOLD_PX;
    };

    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || userScrolledUpRef.current) return;
    container.scrollTop = container.scrollHeight;
  }, [dependency]);

  return containerRef;
}
