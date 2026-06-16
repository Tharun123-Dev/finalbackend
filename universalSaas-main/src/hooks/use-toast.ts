import { useCallback } from "react";

/**
 * Minimal toast hook used throughout the app.
 * It provides `toast`, `success` and `error` helpers.
 * For a production‑grade solution you would replace this
 * with the real shadcn/ui/sonner implementation.
 */
export function useToast() {
  const toast = useCallback(
    (options: { title: string; description?: string; variant?: string }) => {
      const { title, description } = options;
      // Simple alert for demo purposes – replace with UI toast later
      alert(`${title}${description ? ": " + description : ""}`);
    },
    []
  );

  const success = useCallback((message: string) => {
    alert(`✅ ${message}`);
  }, []);

  const error = useCallback((message: string) => {
    alert(`❌ ${message}`);
  }, []);

  return { toast, success, error };
}


