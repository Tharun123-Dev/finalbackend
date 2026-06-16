import { INTEGRATIONS_BASE } from '@/config/api'
import { apiRequest } from '@/lib/api-client'
import type {
  IntegrationCardResponse,
  IntegrationConfigureRequest,
  IntegrationDetailsResponse,
  IntegrationTestResponse,
  IntegrationToggleRequest,
  OAuthConnectResponse,
  IntegrationLogResponse,
  SyncHistoryResponse,
  SpringPage,
} from '@/types/integrations-api'

const base = INTEGRATIONS_BASE

export function listIntegrations() {
  return apiRequest<IntegrationCardResponse[]>(base)
}

export function getIntegration(code: string) {
  return apiRequest<IntegrationDetailsResponse>(`${base}/${encodeURIComponent(code)}`)
}

export function toggleIntegration(code: string, body: IntegrationToggleRequest) {
  return apiRequest<IntegrationDetailsResponse>(`${base}/${encodeURIComponent(code)}/toggle`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function configureIntegration(code: string, body: IntegrationConfigureRequest) {
  return apiRequest<IntegrationDetailsResponse>(`${base}/${encodeURIComponent(code)}/configure`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function testIntegration(code: string) {
  return apiRequest<IntegrationTestResponse>(`${base}/${encodeURIComponent(code)}/test`, {
    method: 'POST',
  })
}

export function disconnectIntegration(code: string) {
  return apiRequest<void>(`${base}/${encodeURIComponent(code)}/disconnect`, {
    method: 'POST',
  })
}

export function getIntegrationLogs(code: string, page = 0, size = 20) {
  const params = new URLSearchParams({ page: String(page), size: String(size) })
  return apiRequest<SpringPage<IntegrationLogResponse>>(
    `${base}/${encodeURIComponent(code)}/logs?${params}`
  )
}

export function getSyncHistory(code: string) {
  return apiRequest<SyncHistoryResponse[]>(`${base}/${encodeURIComponent(code)}/sync-history`)
}

export function getOAuthConnectUrl(code: string) {
  return apiRequest<OAuthConnectResponse>(
    `${base}/${encodeURIComponent(code)}/oauth/connect`
  )
}

/** Provider-specific aliases (same response as generic connect). */
export function getGoogleOAuthConnectUrl() {
  return apiRequest<OAuthConnectResponse>(`${base}/google/oauth/connect`)
}

export function getZoomOAuthConnectUrl() {
  return apiRequest<OAuthConnectResponse>(`${base}/zoom/oauth/connect`)
}

export async function startOAuthConnect(code: string) {
  const upper = code.toUpperCase()
  let response: OAuthConnectResponse
  if (upper === 'GOOGLE') {
    response = await getGoogleOAuthConnectUrl()
  } else if (upper === 'ZOOM') {
    response = await getZoomOAuthConnectUrl()
  } else {
    response = await getOAuthConnectUrl(code)
  }
  window.location.href = response.authUrl
}

export function getZapierLogs(page = 0, size = 5) {
  const params = new URLSearchParams({ page: String(page), size: String(size) })
  return fetch(`${base}/zapier/logs?${params}`)
}



