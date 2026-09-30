# Real-Time Data Dashboard — Implementation Plan

## Top-Level Overview

Build a production-ready, full-stack **Real-Time Data Dashboard** (RTDD) web application.
The system ingests, processes, stores, and visualises streaming metric data in real time via WebSockets.
A built-in simulator generates realistic data during development so the full application can be demonstrated without external hardware. The architecture is designed so the simulator can later be replaced by IoT sensors, MQTT brokers, Kafka topics, or any external streaming source without rewriting the frontend or core backend logic.

**Stack decision summary**
- **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts + TanStack Query + Zustand + React Router v6
- **Backend**: Python 3.11 + FastAPI + Uvicorn + SQLAlchemy 2 + Pydantic v2 + python-jose (JWT) + passlib + bcrypt
- **Database**: SQLite for local dev (file-based, zero-config); PostgreSQL for production. Same SQLAlchemy models work for both via `DATABASE_URL`.
- **TimescaleDB decision**: TimescaleDB is a PostgreSQL extension that adds hypertables for efficient time-series queries. It is recommended as the production database upgrade path (Phase 12) but is NOT required in Phase 1. The schema is designed to be TimescaleDB-compatible from day one (using `timestamp` as the leading column in composite indexes on readings tables).
- **State management**: TanStack Query for server state; Zustand for UI/WebSocket/auth state. React Context is used only for theme. Redux Toolkit is not needed at this scale.
- **Charts**: Recharts (React-native, tree-shakeable, good TypeScript support). ECharts is the fallback if advanced gauge/heatmap charts are required in Phase 8.

---

## Architecture Overview (Text Diagram)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
│  Simulator │ REST POST │ IoT Device │ MQTT (future) │ Kafka (future) │
└───────────────────────────┬─────────────────────────────────────────┘
                            │  HTTP POST  /api/ingest
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                                 │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│  │   Auth       │  │  REST API    │  │  WebSocket Server      │    │
│  │  (JWT)       │  │  Routers     │  │  /ws/live              │    │
│  └──────────────┘  └──────┬───────┘  └────────────┬───────────┘    │
│                           │                        │                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Services Layer                                   │  │
│  │  DataService │ AlertService │ NotificationService │ Simulator │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              SQLAlchemy ORM + Alembic Migrations              │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                           │                                         │
└───────────────────────────┼─────────────────────────────────────────┘
                            ▼
                 ┌─────────────────────┐
                 │  SQLite (dev)       │
                 │  PostgreSQL (prod)  │
                 └─────────────────────┘

                  WebSocket (ws://...)
                 ┌─────────────────────┐
                 │   REACT FRONTEND    │
                 │                     │
                 │  Zustand (WS state) │
                 │  TanStack Query     │
                 │  Recharts           │
                 │  shadcn/ui          │
                 └─────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend framework | React 18 + TypeScript | Component model, ecosystem, type safety |
| Build tool | Vite | Fast HMR, ESM-native, excellent TS support |
| Styling | Tailwind CSS v3 | Utility-first, dark mode via `class` strategy |
| Component library | shadcn/ui | Radix-based, accessible, unstyled primitives that extend Tailwind |
| Icons | Lucide React | Tree-shakeable, consistent stroke style |
| Routing | React Router v6 | Industry standard, nested routes, protected routes |
| Server state | TanStack Query v5 | Caching, background refetch, mutation tracking |
| UI/WebSocket state | Zustand | Minimal, no boilerplate, perfect for WS slice |
| Charts | Recharts | React-native, composable, responsive containers |
| HTTP client | Axios | Interceptors for JWT injection/refresh |
| WebSocket client | Native browser WebSocket + custom hook | No library needed; hook handles reconnect |
| Backend framework | FastAPI | Async, auto-generated OpenAPI docs, Pydantic integration |
| ASGI server | Uvicorn | Production-grade ASGI |
| ORM | SQLAlchemy 2 (async) | Supports SQLite + PostgreSQL, Alembic migrations |
| Validation | Pydantic v2 | Fast, type-safe, reused for FastAPI schemas |
| Auth | python-jose + passlib + bcrypt | Industry-standard JWT + password hashing |
| Migrations | Alembic | Schema versioning |
| Database (dev) | SQLite | Zero-config |
| Database (prod) | PostgreSQL | Reliable, indexable, TimescaleDB-compatible |
| Testing (BE) | Pytest + httpx (async) | Async API testing |
| Testing (FE) | Vitest + React Testing Library | Fast, Vite-native |
| Linting (BE) | Ruff + Black | Fast linting + formatting |
| Linting (FE) | ESLint + Prettier | Standard tooling |
| Dev tools | Docker Compose (optional) | Runs PostgreSQL locally without install |

---

## Folder Structure

### Backend

```
backend/
├── app/
│   ├── main.py                  # FastAPI app creation, router registration, CORS, startup
│   ├── config.py                # Settings via pydantic-settings (.env loading)
│   ├── database.py              # Async SQLAlchemy engine, session factory, Base
│   ├── dependencies.py          # get_db(), get_current_user() reusable deps
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User, Role models
│   │   ├── source.py            # DataSource model
│   │   ├── metric.py            # MetricDefinition model
│   │   ├── reading.py           # DataReading (time-series rows)
│   │   ├── alert.py             # AlertRule, AlertEvent models
│   │   ├── notification.py      # Notification model
│   │   ├── dashboard.py         # DashboardConfig model
│   │   └── activity.py          # ActivityLog model
│   ├── schemas/
│   │   ├── auth.py              # LoginRequest, TokenResponse, RegisterRequest
│   │   ├── user.py              # UserRead, UserUpdate
│   │   ├── source.py            # DataSourceCreate, DataSourceRead
│   │   ├── metric.py            # MetricRead
│   │   ├── reading.py           # ReadingCreate, ReadingRead, ReadingPage
│   │   ├── alert.py             # AlertRuleCreate, AlertEventRead
│   │   ├── notification.py      # NotificationRead
│   │   ├── dashboard.py         # DashboardConfigRead/Update
│   │   └── ws.py                # WebSocket message envelope schema
│   ├── routers/
│   │   ├── auth.py              # /api/auth/*
│   │   ├── users.py             # /api/users/*
│   │   ├── sources.py           # /api/sources/*
│   │   ├── metrics.py           # /api/metrics/*
│   │   ├── data.py              # /api/data/*
│   │   ├── alerts.py            # /api/alerts/*
│   │   ├── notifications.py     # /api/notifications/*
│   │   ├── dashboard.py         # /api/dashboard/*
│   │   └── reports.py           # /api/reports/*
│   ├── services/
│   │   ├── auth_service.py      # Token creation, password hashing/verify
│   │   ├── data_service.py      # Ingest, query, aggregate readings
│   │   ├── alert_service.py     # Evaluate rules, create events
│   │   ├── notification_service.py # Create, read, mark notifications
│   │   ├── report_service.py    # Generate report summaries
│   │   └── dashboard_service.py # Get/update dashboard configs
│   ├── websocket/
│   │   ├── manager.py           # ConnectionManager: register, broadcast, disconnect
│   │   └── router.py            # WS endpoint /ws/live, auth handshake
│   ├── auth/
│   │   ├── jwt.py               # create_access_token, decode_token
│   │   └── middleware.py        # verify_token dependency
│   ├── simulator/
│   │   ├── engine.py            # Async background task; generates readings
│   │   └── metrics_config.py    # Default metric definitions (temp, humidity, etc.)
│   └── utils/
│       ├── logger.py            # Structured logging setup
│       ├── pagination.py        # PageParams helper
│       └── time.py              # UTC now, range helpers
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py              # Async test client, in-memory DB fixtures
│   ├── test_auth.py
│   ├── test_data.py
│   ├── test_alerts.py
│   └── test_websocket.py
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── Dockerfile
```

### Frontend

```
frontend/
├── src/
│   ├── main.tsx                 # React root, QueryClientProvider, RouterProvider
│   ├── App.tsx                  # Route definitions
│   ├── types/
│   │   ├── auth.ts              # User, Role, Token types
│   │   ├── data.ts              # Reading, Metric, DataSource types
│   │   ├── alert.ts             # AlertRule, AlertEvent types
│   │   ├── notification.ts      # Notification type
│   │   ├── dashboard.ts         # DashboardConfig, KpiCard types
│   │   └── ws.ts                # WS message envelope type
│   ├── api/
│   │   ├── client.ts            # Axios instance, JWT interceptor, refresh logic
│   │   ├── auth.ts              # login(), register(), refresh()
│   │   ├── data.ts              # getReadings(), postReading(), getHistory()
│   │   ├── sources.ts           # CRUD for data sources
│   │   ├── alerts.ts            # CRUD for alert rules
│   │   ├── notifications.ts     # getNotifications(), markRead()
│   │   ├── dashboard.ts         # getSummary(), getConfig()
│   │   └── reports.ts           # generateReport(), exportReport()
│   ├── store/
│   │   ├── authStore.ts         # Zustand: user, token, login/logout actions
│   │   ├── wsStore.ts           # Zustand: WS status, latest readings buffer
│   │   ├── settingsStore.ts     # Zustand: theme, defaultRange, refreshInterval
│   │   └── notificationStore.ts # Zustand: unread count, recent toasts
│   ├── hooks/
│   │   ├── useWebSocket.ts      # WS connect/disconnect/reconnect, feeds wsStore
│   │   ├── useAuth.ts           # Auth actions wrapping authStore
│   │   ├── useMetrics.ts        # TanStack Query hooks for metrics
│   │   ├── useReadings.ts       # TanStack Query hooks for readings/history
│   │   ├── useSources.ts        # TanStack Query hooks for sources
│   │   ├── useAlerts.ts         # TanStack Query hooks for alerts
│   │   ├── useNotifications.ts  # TanStack Query hooks for notifications
│   │   └── useDebounce.ts       # Generic debounce hook for search
│   ├── layouts/
│   │   ├── AppLayout.tsx        # Sidebar + TopNav + main content slot
│   │   ├── AuthLayout.tsx       # Centered card layout for auth pages
│   │   └── ProtectedRoute.tsx   # Redirects to /login if unauthenticated
│   ├── components/
│   │   ├── ui/                  # shadcn/ui generated components (button, card, etc.)
│   │   ├── common/
│   │   │   ├── KpiCard.tsx      # Metric card with sparkline, trend, delta
│   │   │   ├── StatusBadge.tsx  # Connection / severity status pill
│   │   │   ├── DataTable.tsx    # Generic sortable/paginated table
│   │   │   ├── GlobalSearch.tsx # Ctrl+K modal search
│   │   │   ├── ThemeToggle.tsx  # Light/Dark/System toggle
│   │   │   ├── ConnectionStatus.tsx # WS status indicator
│   │   │   ├── NotificationBell.tsx # Badge + popover
│   │   │   ├── SkeletonCard.tsx # Loading skeleton for KPI cards
│   │   │   ├── EmptyState.tsx   # Empty/error state placeholder
│   │   │   └── ExportButton.tsx # CSV/JSON/PDF export trigger
│   │   ├── charts/
│   │   │   ├── LineChart.tsx    # Recharts LineChart wrapper
│   │   │   ├── AreaChart.tsx    # Recharts AreaChart wrapper
│   │   │   ├── BarChart.tsx     # Recharts BarChart wrapper
│   │   │   ├── ScatterChart.tsx
│   │   │   ├── GaugeChart.tsx   # Custom radial gauge (Recharts RadialBar)
│   │   │   ├── SparklineChart.tsx # Mini inline chart for KPI cards
│   │   │   └── ChartContainer.tsx # Responsive wrapper + title + controls
│   │   ├── alerts/
│   │   │   ├── AlertCard.tsx
│   │   │   ├── AlertRuleForm.tsx # Modal form for create/edit alert rules
│   │   │   └── AlertHistory.tsx
│   │   ├── sources/
│   │   │   ├── SourceCard.tsx
│   │   │   └── SourceForm.tsx
│   │   ├── sidebar/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── SidebarNavItem.tsx
│   │   │   └── SidebarFooter.tsx
│   │   └── topnav/
│   │       ├── TopNav.tsx
│   │       └── UserMenu.tsx
│   ├── pages/
│   │   ├── auth/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   ├── ForgotPasswordPage.tsx
│   │   │   └── ResetPasswordPage.tsx
│   │   ├── DashboardPage.tsx    # Home / KPI overview
│   │   ├── LiveDataPage.tsx     # Real-time charts + table
│   │   ├── AnalyticsPage.tsx    # Configurable charts with time ranges
│   │   ├── HistoricalDataPage.tsx # Searchable paginated table
│   │   ├── DataSourcesPage.tsx
│   │   ├── AlertsPage.tsx
│   │   ├── NotificationsPage.tsx
│   │   ├── ReportsPage.tsx
│   │   ├── SettingsPage.tsx
│   │   └── ProfilePage.tsx
│   └── utils/
│       ├── formatters.ts        # Number, date, unit formatting
│       ├── validators.ts        # Zod schemas for forms
│       ├── constants.ts         # Route paths, WS URL, time range options
│       └── export.ts            # CSV, JSON, PDF export helpers
├── public/
│   └── favicon.svg
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── vite.config.ts
├── .eslintrc.cjs
└── .prettierrc
```

---

## Database Schema

### Table: users
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| email | VARCHAR(255) UNIQUE NOT NULL | |
| username | VARCHAR(100) UNIQUE NOT NULL | |
| hashed_password | VARCHAR(255) NOT NULL | bcrypt |
| role | ENUM(admin, user, viewer) DEFAULT user | |
| is_active | BOOLEAN DEFAULT true | |
| avatar_url | VARCHAR(500) NULL | |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| updated_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

### Table: data_sources
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| name | VARCHAR(200) NOT NULL | |
| source_type | ENUM(simulator, rest_api, websocket, iot, csv, database, external_api) | |
| config | JSONB | connection params, update interval, etc. |
| is_enabled | BOOLEAN DEFAULT true | |
| last_seen_at | TIMESTAMPTZ NULL | |
| owner_id | UUID FK → users.id | |
| created_at | TIMESTAMPTZ NOT NULL | |
| updated_at | TIMESTAMPTZ NOT NULL | |

### Table: metric_definitions
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| name | VARCHAR(100) UNIQUE NOT NULL | e.g. "temperature" |
| display_name | VARCHAR(200) NOT NULL | |
| unit | VARCHAR(50) NULL | e.g. "°C" |
| min_value | FLOAT NULL | for gauge scaling |
| max_value | FLOAT NULL | |
| category | VARCHAR(100) NULL | e.g. "environmental" |
| source_id | UUID FK → data_sources.id NULL | |
| created_at | TIMESTAMPTZ NOT NULL | |

### Table: data_readings
| Column | Type | Notes |
|---|---|---|
| id | BIGSERIAL (PK) | use BIGINT for high-volume time-series |
| metric_id | UUID FK → metric_definitions.id | |
| source_id | UUID FK → data_sources.id | |
| value | DOUBLE PRECISION NOT NULL | |
| status | ENUM(normal, warning, critical) DEFAULT normal | |
| timestamp | TIMESTAMPTZ NOT NULL | leading index column |
| created_at | TIMESTAMPTZ NOT NULL DEFAULT now() | |

**Indexes on data_readings:**
- `idx_readings_timestamp` on `(timestamp DESC)`
- `idx_readings_metric_timestamp` on `(metric_id, timestamp DESC)`
- `idx_readings_source_timestamp` on `(source_id, timestamp DESC)`

> TimescaleDB note: In production, convert `data_readings` to a hypertable on `timestamp`. This reduces query time for range scans by orders of magnitude and enables automatic chunk compression.

### Table: alert_rules
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| name | VARCHAR(200) NOT NULL | |
| metric_id | UUID FK → metric_definitions.id | |
| operator | ENUM(gt, lt, gte, lte, eq, neq) | |
| threshold | DOUBLE PRECISION NOT NULL | |
| severity | ENUM(info, warning, critical) | |
| duration_seconds | INTEGER DEFAULT 0 | must be true for N seconds |
| is_enabled | BOOLEAN DEFAULT true | |
| owner_id | UUID FK → users.id | |
| created_at | TIMESTAMPTZ NOT NULL | |

### Table: alert_events
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| rule_id | UUID FK → alert_rules.id | |
| triggered_value | DOUBLE PRECISION NOT NULL | |
| triggered_at | TIMESTAMPTZ NOT NULL | |
| resolved_at | TIMESTAMPTZ NULL | |
| message | TEXT NULL | |

### Table: notifications
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID FK → users.id | |
| title | VARCHAR(300) NOT NULL | |
| body | TEXT NULL | |
| type | ENUM(alert, system, report, connection) | |
| is_read | BOOLEAN DEFAULT false | |
| reference_id | UUID NULL | links to alert_event or other entity |
| created_at | TIMESTAMPTZ NOT NULL | |

### Table: dashboard_configs
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID FK → users.id UNIQUE | one config per user |
| layout | JSONB | widget positions, visible cards |
| default_time_range | VARCHAR(50) DEFAULT '1h' | |
| default_chart_type | VARCHAR(50) DEFAULT 'line' | |
| refresh_interval | INTEGER DEFAULT 5 | seconds |
| created_at | TIMESTAMPTZ NOT NULL | |
| updated_at | TIMESTAMPTZ NOT NULL | |

### Table: user_preferences
| Column | Type | Notes |
|---|---|---|
| id | UUID (PK) | |
| user_id | UUID FK → users.id UNIQUE | |
| theme | ENUM(light, dark, system) DEFAULT system | |
| notifications_enabled | BOOLEAN DEFAULT true | |
| default_export_format | ENUM(csv, json, pdf) DEFAULT csv | |
| data_retention_days | INTEGER DEFAULT 30 | |
| updated_at | TIMESTAMPTZ NOT NULL | |

### Table: activity_logs
| Column | Type | Notes |
|---|---|---|
| id | BIGSERIAL (PK) | |
| user_id | UUID FK → users.id NULL | NULL for system events |
| action | VARCHAR(200) NOT NULL | e.g. "login", "alert_created" |
| resource_type | VARCHAR(100) NULL | |
| resource_id | UUID NULL | |
| ip_address | VARCHAR(45) NULL | |
| metadata | JSONB NULL | |
| created_at | TIMESTAMPTZ NOT NULL | |

---

## API Architecture

### REST Endpoints

```
Authentication
  POST   /api/auth/register           Create new user account
  POST   /api/auth/login              Returns access token + refresh token
  POST   /api/auth/refresh            Exchange refresh token for new access token
  POST   /api/auth/logout             Invalidate refresh token
  POST   /api/auth/forgot-password    Send reset email
  POST   /api/auth/reset-password     Reset password with token

Users (admin only)
  GET    /api/users                   List users
  GET    /api/users/{id}              Get user
  PUT    /api/users/{id}              Update user
  DELETE /api/users/{id}              Delete user

Profile (authenticated user)
  GET    /api/profile                 Get own profile + preferences
  PUT    /api/profile                 Update own profile
  PUT    /api/profile/password        Change password
  PUT    /api/profile/preferences     Update user preferences

Dashboard
  GET    /api/dashboard/summary       KPI summary: total readings, active sources, alert count, avg values
  GET    /api/dashboard/config        Get user's dashboard layout config
  PUT    /api/dashboard/config        Update layout config

Metrics
  GET    /api/metrics                 List all metric definitions
  GET    /api/metrics/{id}            Get single metric
  POST   /api/metrics                 Create metric definition (admin)
  PUT    /api/metrics/{id}            Update metric (admin)
  DELETE /api/metrics/{id}            Delete metric (admin)

Data
  GET    /api/data                    Latest reading per metric (live snapshot)
  GET    /api/data/history            Paginated historical readings (filters: metric, source, start, end, status)
  POST   /api/data/ingest             Ingest one or more readings (for external sources)

Data Sources
  GET    /api/sources                 List sources
  GET    /api/sources/{id}            Get source
  POST   /api/sources                 Create source
  PUT    /api/sources/{id}            Update source
  DELETE /api/sources/{id}            Delete source
  POST   /api/sources/{id}/enable     Enable source
  POST   /api/sources/{id}/disable    Disable source

Alert Rules
  GET    /api/alerts/rules            List alert rules
  POST   /api/alerts/rules            Create rule
  PUT    /api/alerts/rules/{id}       Update rule
  DELETE /api/alerts/rules/{id}       Delete rule
  GET    /api/alerts/events           List triggered alert events (filterable)

Notifications
  GET    /api/notifications           List notifications for current user
  POST   /api/notifications/{id}/read Mark single as read
  POST   /api/notifications/read-all  Mark all as read
  DELETE /api/notifications/{id}      Delete notification

Reports
  GET    /api/reports                 List generated reports
  POST   /api/reports                 Generate a new report (daily/weekly/monthly/custom)
  GET    /api/reports/{id}            Get report data
  GET    /api/reports/{id}/export     Download report as PDF/CSV/JSON

Simulator
  GET    /api/simulator/status        Current simulator state
  POST   /api/simulator/start         Start background simulator
  POST   /api/simulator/stop          Stop simulator
  PUT    /api/simulator/config        Update simulator parameters
```

### WebSocket

```
WS  /ws/live?token={access_token}

  Client connects, token is validated on handshake.
  Server sends typed JSON messages:

  Outbound message envelope:
  {
    "type": "reading" | "alert" | "notification" | "status" | "ping",
    "payload": { ... },
    "timestamp": "ISO8601"
  }

  reading payload:
  {
    "metric": "temperature",
    "value": 28.6,
    "unit": "°C",
    "source": "sensor-01",
    "status": "normal",
    "timestamp": "..."
  }

  alert payload:
  {
    "rule_id": "...",
    "rule_name": "High Temperature",
    "severity": "critical",
    "triggered_value": 42.1,
    "message": "temperature exceeded threshold of 40°C"
  }

  status payload:
  {
    "active_sources": 3,
    "data_rate": 4.2,        // readings per second
    "simulator_running": true
  }
```

---

## Navigation Hierarchy

```
/ (AppLayout)
├── /dashboard                (DashboardPage — default landing)
├── /live                     (LiveDataPage)
├── /analytics                (AnalyticsPage)
├── /history                  (HistoricalDataPage)
├── /sources                  (DataSourcesPage)
├── /alerts                   (AlertsPage)
├── /notifications             (NotificationsPage)
├── /reports                  (ReportsPage)
├── /settings                  (SettingsPage)
└── /profile                  (ProfilePage)

/auth (AuthLayout — public)
├── /auth/login
├── /auth/register
├── /auth/forgot-password
└── /auth/reset-password/:token
```

---

## Page-by-Page Specification

### DashboardPage (`/dashboard`)
- 6 KPI cards: Total Readings (24h), Active Sources, Avg Temperature, Active Alerts, Data Rate (readings/s), System Status
- Mini sparkline per KPI showing last 30 data points
- Recent alerts panel (last 5 alert events)
- Active sources status grid
- Latest readings table (last 20 rows)

### LiveDataPage (`/live`)
- Full-width real-time line chart updating on every WS message
- Metric selector (dropdown) and source selector
- Chart type toggle: Line / Area / Bar
- Live data table (newest-first, 50 rows, auto-scroll or pause-on-hover)
- Controls: Pause, Resume, Reconnect, Fullscreen
- Connection status indicator always visible

### AnalyticsPage (`/analytics`)
- Time range selector (5m / 15m / 1h / today / yesterday / 7d / 30d / custom)
- Multi-metric selector (compare up to 4 metrics on same chart)
- Chart type selector
- Aggregation selector (raw / avg per minute / avg per hour)
- Zoom via chart brush component
- Download chart data button (CSV)

### HistoricalDataPage (`/history`)
- Date-time range picker
- Metric filter (multi-select)
- Source filter (multi-select)
- Status filter (normal / warning / critical)
- Global search input
- Sortable columns: timestamp, metric, value, unit, source, status
- Pagination (25/50/100 per page)
- Column visibility toggle
- Export CSV / JSON / PDF buttons

### DataSourcesPage (`/sources`)
- Card grid showing each source: name, type, status, last seen, data rate
- Add Source button → modal form (shadcn Dialog)
- Edit / Delete per card
- Enable/Disable toggle per card
- Source form fields: name, type, config (dynamic based on type), update interval

### AlertsPage (`/alerts`)
- Two tabs: Rules and Events
- Rules tab: list of configured alert rules with severity badge, enabled toggle, edit/delete
- Create Rule button → modal form
- Events tab: history of triggered alerts, filterable by severity and date
- Alert rule form: metric, operator, threshold, severity, duration, name

### NotificationsPage (`/notifications`)
- Full notification list for current user
- Filter by type and read status
- Mark all as read button
- Delete individual notifications
- Each notification shows: icon, title, body, timestamp, relative time

### ReportsPage (`/reports`)
- List of generated reports (type, date range, created at)
- Generate Report button: choose type (daily/weekly/monthly/custom) and date range
- View report: KPI summary, charts preview, alert summary
- Export buttons: PDF, CSV, JSON

### SettingsPage (`/settings`)
- Appearance: Theme selector (light/dark/system) with live preview
- Dashboard defaults: default time range, chart type, refresh interval, landing page
- Notifications: enable/disable toggles per type
- Data: retention days, default export format

### ProfilePage (`/profile`)
- Display: avatar, name, email, role, member since
- Edit profile form (name, avatar URL)
- Change password form (current + new + confirm)
- Logout button
- Danger zone: delete account (admin protected)

### Auth Pages
- Login: email + password, "Remember me", link to forgot password
- Register: username, email, password, confirm password
- Forgot Password: email input → success message
- Reset Password: new password + confirm, validates token from URL

---

## Component Architecture

### Layout Components
- `AppLayout` — outer shell with sidebar, top nav, scrollable main area. Collapses sidebar on mobile via `useSidebar` hook.
- `AuthLayout` — centered card, gradient background, no navigation.
- `ProtectedRoute` — reads `authStore`, redirects to `/auth/login` if no valid token.

### KpiCard
Props: `title, value, unit, change, changePercent, trend ("up"|"down"|"flat"), sparklineData[], status, timestamp`
Displays: value + unit large, delta badge, trend arrow, mini sparkline, last updated.

### DataTable (generic)
Props: `columns[], data[], loading, pagination, onSort, onPageChange, searchable`
Features: column header sort, skeleton rows while loading, empty state, row actions slot.

### ChartContainer
Props: `title, children, controls?, loading, onExport, fullscreenable`
Wraps any Recharts chart with: title bar, controls row, responsive container, skeleton overlay, fullscreen button.

### useWebSocket hook
- Opens `WebSocket` to `/ws/live?token=...`
- Manages `readyState` → updates `wsStore` status (CONNECTED / RECONNECTING / DISCONNECTED)
- Exponential backoff reconnect (max 30s)
- Dispatches incoming messages to `wsStore.pushReading()` and `notificationStore.pushToast()`
- Sends heartbeat ping every 20s

### GlobalSearch (Ctrl+K)
- `cmdk` or custom command palette
- Searches metrics, sources, alerts, historical records (debounced API call)
- Keyboard navigable result list

---

## Real-Time Data Flow

```
1. Simulator (backend async task, runs every N ms)
   └─ Generates ReadingCreate payload for each enabled metric

2. data_service.ingest_reading(reading)
   ├─ Validates against metric definition
   ├─ Determines status (normal/warning/critical based on thresholds)
   ├─ Inserts row into data_readings table
   └─ Returns persisted ReadingRead

3. alert_service.evaluate(reading)
   ├─ Loads all enabled alert rules for this metric
   ├─ Evaluates operator/threshold
   ├─ If triggered: creates alert_event, creates notification, logs activity
   └─ Returns list of triggered AlertEvent

4. websocket.manager.broadcast(message)
   ├─ Serialises ReadingRead + triggered alerts to WS envelope JSON
   └─ Sends to all authenticated connected clients

5. Frontend useWebSocket hook receives message
   ├─ type="reading" → wsStore.pushReading(payload)
   │   ├─ Maintains ring buffer of last 200 readings per metric
   │   └─ TanStack Query cache invalidated for /api/data
   ├─ type="alert" → notificationStore.pushToast(alert)
   │   └─ Toast notification shown via shadcn Toaster
   └─ type="status" → wsStore.setStatus(payload)

6. React components subscribe to wsStore slices
   ├─ LiveDataPage: re-renders chart with new ring buffer data
   ├─ KpiCard: reads latest value per metric
   ├─ ConnectionStatus: reads wsStore.connectionState
   └─ NotificationBell: reads notificationStore.unreadCount
```

---

## Authentication Flow

```
1. User submits login form
2. POST /api/auth/login → backend verifies email + bcrypt password
3. Returns { access_token (15min JWT), refresh_token (7d JWT) }
4. Frontend stores access_token in memory (authStore), refresh_token in httpOnly cookie (or localStorage with awareness)
5. Axios interceptor attaches Authorization: Bearer {access_token} to every request
6. On 401: interceptor calls POST /api/auth/refresh, gets new access_token, retries original request
7. On refresh failure: authStore.logout(), redirect to /auth/login

JWT payload: { sub: user_id, role: "admin"|"user"|"viewer", exp, iat }

Protected route: ProtectedRoute wrapper reads authStore.user; if null, redirects to login.

Role-based access:
  admin  → full access including user management, all data source types
  user   → create/edit own sources, alerts, dashboard config; read all data
  viewer → read-only access to dashboard, history, analytics; no mutations

WebSocket auth:
  Token passed as query param ?token=... on initial connect (before HTTP upgrade).
  Backend validates token before accepting the WS connection.
  If token expires, client re-fetches access token via refresh and reconnects.
```

---

## Alert Flow

```
1. User creates AlertRule via POST /api/alerts/rules
   { metric_id, operator: "gt", threshold: 40.0, severity: "critical", duration_seconds: 0 }

2. alert_service caches active rules in memory (reloaded on CRUD changes)

3. On every ingested reading:
   alert_service.evaluate(reading):
   ├─ Find rules matching reading.metric_id
   ├─ For each rule: apply operator comparison (e.g. value > threshold)
   ├─ If duration_seconds > 0: use a sliding window buffer; only fire if condition
   │   held true for the required duration
   ├─ If triggered AND no open event for this rule → create AlertEvent
   ├─ If resolved (condition no longer true) AND open event exists → set resolved_at
   └─ Create Notification for the alerting user/all users (based on rule ownership)

4. Triggered AlertEvent is included in the next WS broadcast

5. Frontend receives type="alert" message:
   ├─ Shows toast notification with severity styling
   ├─ Increments notification badge count
   └─ Invalidates TanStack Query cache for /api/alerts/events

6. User views AlertsPage → sees Events tab with full history
```

---

## Development Phases

### Phase 1 — Project Initialisation [ ] pending
- Create `backend/` and `frontend/` directories
- Initialise Git repo, add `.gitignore`, create `.env.example`
- Backend: `python -m venv venv`, install FastAPI, Uvicorn, SQLAlchemy, Alembic, etc.
- Frontend: `npm create vite@latest frontend -- --template react-ts`
- Install Tailwind CSS, shadcn/ui, React Router, TanStack Query, Zustand, Axios, Recharts
- Configure ESLint, Prettier, Ruff, Black
- Confirm `uvicorn app.main:app --reload` and `npm run dev` both start

### Phase 2 — Database & Models [ ] pending
- Write all SQLAlchemy models (users, sources, metrics, readings, alert_rules, alert_events, notifications, dashboard_configs, user_preferences, activity_logs)
- Configure Alembic, run initial migration
- Seed script: default metric definitions, default admin user
- Verify tables created in SQLite dev DB

### Phase 3 — Backend Authentication [ ] pending
- Implement JWT creation/validation in `auth/jwt.py`
- Implement `auth_service.py`: hash password, verify password, create user
- Implement `/api/auth/login`, `/api/auth/register`, `/api/auth/refresh`, `/api/auth/logout`
- Add `get_current_user` FastAPI dependency
- Write pytest tests for auth endpoints

### Phase 4 — Core REST API [ ] pending
- Implement all routers: users, profile, sources, metrics, data, alerts, notifications, dashboard, reports
- Implement corresponding services
- Add role-based access guards using dependency injection
- Verify all endpoints in Swagger UI (`/docs`)
- Write basic pytest tests for each router

### Phase 5 — Data Simulator [ ] pending
- Implement `simulator/metrics_config.py`: define default metrics (temperature, humidity, pressure, heart_rate, speed, voltage, current, system_load, network_latency)
- Implement `simulator/engine.py`: FastAPI startup background task that calls `data_service.ingest_reading()` on a configurable interval
- Add simulator control endpoints (`/api/simulator/start`, `/api/simulator/stop`, `/api/simulator/config`)
- Verify readings appearing in database

### Phase 6 — WebSocket Server [ ] pending
- Implement `websocket/manager.py`: `ConnectionManager` with `connect`, `disconnect`, `broadcast`
- Implement `websocket/router.py`: `/ws/live` endpoint with token auth on upgrade
- Wire `data_service.ingest_reading()` to call `manager.broadcast()` after each ingestion
- Wire `alert_service.evaluate()` results into broadcast
- Test with browser WebSocket client or Postman

### Phase 7 — Frontend Shell [ ] pending
- Configure React Router routes, `AppLayout`, `AuthLayout`, `ProtectedRoute`
- Implement `authStore` (Zustand), login/register pages, JWT interceptor in Axios client
- Implement `wsStore` and `useWebSocket` hook
- Implement `Sidebar`, `TopNav`, `ConnectionStatus`, `ThemeToggle`, `NotificationBell`
- Verify navigation works and authenticated routes redirect correctly

### Phase 8 — Dashboard & Live Data Pages [ ] pending
- Implement `KpiCard`, `SparklineChart`, `ChartContainer`
- Implement `DashboardPage`: fetch summary, render 6 KPI cards, recent alerts, source status
- Implement `LiveDataPage`: subscribe to `wsStore`, render real-time `LineChart`, live table, pause/resume controls

### Phase 9 — Analytics & Historical Pages [ ] pending
- Implement `AnalyticsPage`: time range picker, multi-metric selector, aggregation selector, chart types
- Implement `HistoricalDataPage`: `DataTable` with filters, search, sort, pagination
- Implement export (CSV, JSON) for historical data

### Phase 10 — Alerts & Notifications [ ] pending
- Implement `AlertsPage` (rules tab + events tab), `AlertRuleForm` modal
- Implement alert evaluation backend logic with duration window
- Implement `NotificationsPage`, mark-read logic
- Wire toast notifications in frontend for incoming WS alert messages

### Phase 11 — Data Sources, Reports, Profile, Settings [ ] pending
- Implement `DataSourcesPage` with source CRUD, enable/disable
- Implement `ReportsPage` with report generation and export
- Implement `ProfilePage` and `SettingsPage`
- Implement `GlobalSearch` (Ctrl+K)
- Verify theme persistence (localStorage via `settingsStore`)

### Phase 12 — Testing & Polish [ ] pending
- Backend: write full pytest test suite (auth, CRUD, WS, simulator)
- Frontend: Vitest component tests for KpiCard, DataTable, ChartContainer, useWebSocket
- Add skeleton loaders, empty states, error boundaries to all pages
- Accessibility audit: ARIA labels, keyboard nav, focus rings, contrast
- Performance: profile WS message rate, verify memoization on chart components

### Phase 13 — Production Configuration & Deployment [ ] pending
- Switch `DATABASE_URL` to PostgreSQL, run migrations on prod DB
- Configure CORS for production domain
- Add rate limiting (`slowapi`)
- Create `Dockerfile` for backend, `Dockerfile` for frontend (Nginx static)
- Create `docker-compose.prod.yml`
- Write deployment instructions: Render/Railway (backend), Vercel/Netlify (frontend)
- Create complete `README.md`

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| WebSocket connection drops under load | Medium | High | Exponential backoff reconnect in `useWebSocket`; server-side ping/pong keepalive |
| High-frequency WS messages causing React re-renders | High | Medium | Ring buffer in `wsStore` (max 200 readings); chart updates batched with `requestAnimationFrame`; `React.memo` on chart wrappers |
| JWT refresh token race condition | Medium | High | Single in-flight refresh promise; queue concurrent requests until resolved |
| SQLite not supporting concurrent writes under load | Low (dev only) | Low | Acceptable for dev; switch to PostgreSQL before load testing |
| Large historical queries timing out | Medium | Medium | Pagination, indexed queries, database-side aggregation |
| Hosting platform dropping WebSocket connections | Medium | High | Verify Render/Railway WS support; document fallback (SSE) |
| Alembic migration failures on production | Low | High | Test migrations on staging DB first; keep rollback scripts |
| shadcn/ui version conflicts with Radix | Low | Low | Pin exact versions in package.json |
| CORS misconfiguration blocking WS upgrade | Low | High | Test WS auth from production frontend URL before release |

---

## Testing Plan

### Backend (Pytest)
- `test_auth.py`: register, login, invalid credentials, token refresh, role access
- `test_data.py`: ingest reading, retrieve history with filters, pagination
- `test_sources.py`: CRUD for data sources, enable/disable
- `test_alerts.py`: create rule, trigger evaluation, verify event created, verify notification created
- `test_websocket.py`: connect with valid/invalid token, receive broadcast message
- `test_simulator.py`: start/stop simulator, verify readings appear in DB

### Frontend (Vitest + React Testing Library)
- `KpiCard.test.tsx`: renders value, unit, trend; handles null data
- `DataTable.test.tsx`: sorts, paginates, shows skeleton
- `useWebSocket.test.ts`: mocked WS server; tests CONNECTED state and message dispatch
- `LoginPage.test.tsx`: form validation, success redirect, error display
- `ProtectedRoute.test.tsx`: unauthenticated redirect

### End-to-End (manual or Playwright in future)
1. Register → Login → Dashboard loads with KPI cards
2. Simulator starts → Live Data page shows updating chart
3. Create alert rule → simulator triggers it → toast appears
4. Historical page → filter by metric + date range → export CSV
5. Create data source → disable it → verify data stops
6. Change theme → refresh → theme persists
7. Logout → protected route redirects to login

---

## Deployment Plan

### Frontend (Vercel — recommended)
```
Build command: npm run build
Output dir:    dist
Environment:   VITE_API_URL=https://your-backend.onrender.com
               VITE_WS_URL=wss://your-backend.onrender.com
```

### Backend (Render Web Service)
```
Runtime:       Python 3.11
Build command: pip install -r requirements.txt && alembic upgrade head
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Environment:   DATABASE_URL, JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, FRONTEND_URL
```

### Database (Render PostgreSQL or Supabase)
- Provision managed PostgreSQL
- Set `DATABASE_URL` in backend environment
- Optionally enable TimescaleDB extension for production time-series performance

### WebSocket support
- Render supports persistent WebSocket connections on paid plans
- Railway and Fly.io both support WebSockets on all plans
- Netlify does NOT support backend WebSockets (frontend host only)

---

## Future Expansion

| Capability | Integration Path |
|---|---|
| ESP32 / Arduino | Device POSTs to `/api/data/ingest` over HTTP or opens WS to `/ws/live` |
| IoT sensors (MQTT) | Add `mqtt_listener.py` service that subscribes to MQTT topics and calls `data_service.ingest_reading()` |
| Apache Kafka | Add Kafka consumer in `services/kafka_consumer.py`; same ingestion pipeline |
| Redis Pub/Sub | Replace in-process `ConnectionManager.broadcast()` with Redis pub/sub for horizontal scaling |
| TimescaleDB | Add TimescaleDB to PostgreSQL, convert `data_readings` hypertable; zero model changes required |
| MQTT broker | Mosquitto + `aiomqtt` async client |
| AI/ML predictions | Add `/api/predictions` router; serve scikit-learn or ONNX model; predictions rendered as dashed overlay line on charts |
| Anomaly detection | Rolling z-score or Isolation Forest on ingested readings; auto-creates alert events |
| Wearables / BLE | BLE gateway (Raspberry Pi) that POSTs to ingestion API |
| External APIs | New `source_type: external_api` in DataSource; `poller_service.py` periodically fetches and ingests |
| Grafana integration | Expose Prometheus `/metrics` endpoint via `prometheus-fastapi-instrumentator` |
