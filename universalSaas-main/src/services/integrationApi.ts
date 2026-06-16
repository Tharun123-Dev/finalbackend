export interface Integration {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  connected: boolean;
  color?: string;
}

const API_BASE = import.meta.env.VITE_ROLES_API_BASE
  ? `${import.meta.env.VITE_ROLES_API_BASE}/api`
  : (import.meta.env.VITE_API_BASE_URL ?? '/api');
const INTEGRATIONS_ENDPOINT = `${API_BASE}/integrations`;

export const integrationApi = {
  fetchIntegrations: async (): Promise<Integration[]> => {
    const res = await fetch(INTEGRATIONS_ENDPOINT);
    if (!res.ok) throw new Error('Failed to fetch integrations');
    return res.json();
  },
  connectGoogle: async () => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/google/connect?scopes=https://www.googleapis.com/auth/calendar.events openid email profile`);
  },
  googleCallback: async (code: string) => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/google/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
  },
  connectZoom: async () => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/zoom/connect`);
  },
  zoomCallback: async (code: string) => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/zoom/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
  },
  saveMetaPixel: async (pixelId: string) => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/meta/pixel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pixelId }),
    });
  },
  saveCashfreeConfig: async (config: { appId: string; secretKey: string; mode: string; successRedirectUrl: string; failureRedirectUrl: string }) => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/cashfree/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
  },
  saveWhatsAppConfig: async (cfg: { number: string; apiKey: string }) => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/whatsapp/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg),
    });
  },
  fetchWebhooks: async () => {
    const res = await fetch(`${INTEGRATIONS_ENDPOINT}/webhooks`);
    if (!res.ok) throw new Error('Failed to fetch webhooks');
    return res.json();
  },
  createWebhook: async (payload: { url: string; events: string[] }) => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/webhooks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
  generateApiKey: async () => {
    return fetch(`${INTEGRATIONS_ENDPOINT}/apikey`, { method: 'POST' });
  },
  fetchApiKey: async () => {
    const res = await fetch(`${INTEGRATIONS_ENDPOINT}/apikey`);
    if (!res.ok) throw new Error('Failed to fetch API key');
    return res.json();
  },
  // ---------- Zoom ----------
  configureZoom: async (payload: {
    clientId: string;
    clientSecret: string;
    redirectUri: string;
    scopes: string;
  }) => fetch(`${INTEGRATIONS_ENDPOINT}/zoom/configure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }),
  getZoomStatus: async () => fetch(`${INTEGRATIONS_ENDPOINT}/zoom/status`),
  getZoomConnectUrl: async () => fetch(`${INTEGRATIONS_ENDPOINT}/zoom/connect-url`),
  createZoomMeeting: async (payload: {
    topic: string;
    agenda?: string;
    startTime: string;
    durationMinutes: number;
    timezone: string;
    module: string;
    referenceId: number;
  }) => fetch(`${INTEGRATIONS_ENDPOINT}/zoom/meetings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }),
  updateZoomMeeting: async (meetingId: string | number, payload: {
    topic?: string;
    agenda?: string;
    startTime?: string;
    durationMinutes?: number;
    timezone?: string;
    module?: string;
    referenceId?: number;
  }) => fetch(`${INTEGRATIONS_ENDPOINT}/zoom/meetings/${meetingId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }),
  deleteZoomMeeting: async (meetingId: string | number) => fetch(`${INTEGRATIONS_ENDPOINT}/zoom/meetings/${meetingId}`, { method: 'DELETE' }),
  testZoomConnection: async () => fetch(`${INTEGRATIONS_ENDPOINT}/zoom/test`),
  // ---------- Zapier ----------
  configureZapierWebhook: async (payload: { webhookUrl: string; events?: string[] }) =>
    fetch(`${INTEGRATIONS_ENDPOINT}/zapier/configure-webhook`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  testZapier: async () =>
    fetch(`${INTEGRATIONS_ENDPOINT}/zapier/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    }),
  getZapierStatus: async () =>
    fetch(`${INTEGRATIONS_ENDPOINT}/zapier/status`),
  getZapierLogs: async (page: number = 0, size: number = 5) =>
    fetch(`${INTEGRATIONS_ENDPOINT}/zapier/logs?page=${page}&size=${size}`),
};


