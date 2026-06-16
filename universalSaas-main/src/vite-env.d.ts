/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_ROLES_API_BASE?: string
  readonly VITE_LAP_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

