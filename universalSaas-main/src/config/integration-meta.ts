/** Brand colors when API omits `color` on integration cards. */
export const INTEGRATION_COLORS: Record<string, string> = {
  GOOGLE: '#4285F4',
  WHATSAPP: '#25D366',
  META: '#1877F2',
  ZAPIER: '#FF4A00',
  ZOOM: '#2D8CFF',
  CASHFREE: '#00C853',
  WEBHOOKS: '#6366f1',
}

export function integrationColor(code: string | undefined | null, apiColor?: string | null): string {
  // If API provides a color, use it directly.
  if (apiColor) return apiColor;
  // Guard against missing or non‑string codes.
  if (!code) return '#6366f1';
  return INTEGRATION_COLORS[code.toUpperCase()] ?? '#6366f1';
}

/** Integrations that use OAuth connect instead of API keys only */
export const OAUTH_INTEGRATIONS = new Set(['GOOGLE', 'ZOOM', 'META'])

export function normalizeHealth(
  health?: string | null
): 'healthy' | 'warning' | 'error' {
  const h = (health ?? '').toLowerCase()
  if (h === 'healthy' || h === 'ok' || h === 'up' || h === 'connected') return 'healthy'
  if (h.includes('warn')) return 'warning'
  if (h.includes('error') || h.includes('fail') || h === 'down') return 'error'
  return 'healthy'
}


