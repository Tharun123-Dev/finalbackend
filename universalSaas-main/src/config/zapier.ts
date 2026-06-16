// Zapier configuration constants
// Reads the webhook URL from Vite environment variables.
// Vite exposes env vars prefixed with VITE_ via import.meta.env.
export const ZAPIER_WEBHOOK_URL = (import.meta.env?.VITE_ZAPIER_WEBHOOK_URL as string) || '';



