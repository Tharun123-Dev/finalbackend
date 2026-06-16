# Universal SaaS Dashboard

Enterprise-grade, multi-tenant Universal SaaS platform frontend built with React, Tailwind CSS, Shadcn-style UI primitives, Framer Motion, Lucide React, and Recharts.

## Features

- **Configurable architecture** — Dynamic navigation, modules, and permissions via `src/config/`
- **Premium dashboard** — Stats, charts, activity timeline, quick actions
- **Full module UIs** — Reports, Integrations, Messages, Tickets, Website Builder, Marketing, HRMS, Vendor, Settings
- **Collapsible sidebar** — Grouped modules with badges and active states
- **Enterprise header** — Search, company/branch selectors, theme toggle, notifications, profile
- **Light/dark theme** — Toggle with persistence

## Tech Stack

- React 19 + TypeScript + Vite
- Tailwind CSS v4
- Radix UI (Shadcn-style components)
- Framer Motion
- Recharts
- React Router v7

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Project Structure

```
src/
├── config/          # Navigation, modules, mock data
├── context/         # App (tenant, sidebar) & theme providers
├── components/
│   ├── ui/          # Reusable UI primitives
│   ├── layout/      # Sidebar, Header, AppLayout
│   ├── dashboard/   # Dashboard widgets
│   └── shared/      # PageHeader, etc.
├── pages/           # Route-level module pages
├── routes/          # React Router configuration
├── types/           # Shared TypeScript types
└── lib/             # Utilities
```

## Integrations API

The Integrations page calls your Spring backend at `VITE_API_BASE_URL` (default `http://100.85.146.60:8080/api`).

| UI action | Endpoint |
|-----------|----------|
| Load cards | `GET /integrations` |
| Detail panel | `GET /integrations/{code}` |
| Enable toggle | `POST /integrations/{code}/toggle` |
| Save settings | `POST /integrations/{code}/configure` |
| Test | `POST /integrations/{code}/test` |
| Disconnect | `POST /integrations/{code}/disconnect` |
| OAuth | `GET /integrations/{code}/oauth/connect` (or `/google/oauth/connect`, `/zoom/oauth/connect`) |
| Logs | `GET /integrations/{code}/logs?page=&size=` |
| Sync history | `GET /integrations/{code}/sync-history` |

OAuth callback: backend redirects to `http://localhost:5173/integrations?connected=GOOGLE`.

Set JWT in `localStorage` as `auth_token` if your API requires `Authorization: Bearer`.

Copy `.env.example` to `.env.development` to change the backend IP.

## Extending

1. Add modules in `src/config/modules.ts`
2. Add nav items in `src/config/navigation.ts`
3. Create pages under `src/pages/` and register in `src/routes/index.tsx`
4. Wire backend APIs via context hooks when ready
