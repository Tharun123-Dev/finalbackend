export type IntegrationHealth = 'healthy' | 'warning' | 'error' | string

export interface IntegrationCardResponse {
  id: string
  code: string
  name: string
  description: string
  color?: string
  enabled: boolean
  connected: boolean
  health: IntegrationHealth
  lastSynced?: string | null
  environment?: string | null
}

export interface IntegrationDetailsResponse {
  code: string
  name: string
  description: string
  enabled: boolean
  connected: boolean
  health: IntegrationHealth
  environment?: string | null
  webhookUrl?: string | null
  apiKeyMasked?: string | null
  apiSecretMasked?: string | null
  lastSynced?: string | null
}

export interface IntegrationToggleRequest {
  enabled: boolean
}

export interface IntegrationConfigureRequest {
  apiKey?: string
  apiSecret?: string
  webhookUrl?: string
  environment?: string
  settings?: Record<string, string>
}

export interface IntegrationTestResponse {
  health: string
  status: string
}

export interface IntegrationLogResponse {
  timestamp: string
  level: string
  message: string
  statusCode?: number | null
  payload?: string | null
}

export interface SyncHistoryResponse {
  runId: string
  startTime: string
  endTime?: string | null
  status: string
  description?: string | null
  recordsProcessed?: number | null
  recordsSuccess?: number | null
  recordsFailed?: number | null
}

export interface OAuthConnectResponse {
  authUrl: string
}

export interface ApiErrorBody {
  timestamp?: string
  status?: number
  error?: string
  message?: string
  path?: string
}

export interface SpringPage<T> {
  content: T[]
  totalElements: number
  totalPages: number
  number: number
  size: number
  first?: boolean
  last?: boolean
}

