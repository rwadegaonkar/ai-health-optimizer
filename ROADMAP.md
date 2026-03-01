# AI Health Optimizer — 12-Week Execution Roadmap

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    Next.js 14 + TailwindCSS                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │Dashboard │ │ Food Log │ │Wearables │ │ Insights │           │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API
┌───────────────────────────┴─────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Layer (v1)                        │    │
│  │  /auth  /users  /food  /wearables  /insights  /fitbit   │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────────────┐    │
│  │                  Service Layer                           │    │
│  │  NutritionService  FoodVisionService  CoachingService    │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│  ┌──────────────────────┴──────────────────────────────────┐    │
│  │              AI Decision Engine                          │    │
│  │  ┌────────────┐ ┌──────────────┐ ┌──────────────────┐   │    │
│  │  │ Recovery   │ │Training Load │ │ Energy Balance   │   │    │
│  │  │ Model      │ │ Model        │ │ Model            │   │    │
│  │  └────────────┘ └──────────────┘ └──────────────────┘   │    │
│  │  ┌────────────┐ ┌──────────────┐ ┌──────────────────┐   │    │
│  │  │ Behavioral │ │ Weekly       │ │ Adaptive Policy  │   │    │
│  │  │ Patterns   │ │ Optimizer    │ │ Engine           │   │    │
│  │  └────────────┘ └──────────────┘ └──────────────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────┐  ┌───────────────────────────────┐    │
│  │  CV Pipeline          │  │  Integrations                 │    │
│  │  GPT-4o Vision        │  │  Fitbit OAuth2 + Data Sync    │    │
│  │  Nutritionix Lookup   │  │  Apple Health (V2)            │    │
│  └──────────────────────┘  └───────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│                     DATA LAYER                                   │
│  ┌──────────────┐  ┌───────────────┐  ┌───────────────────┐     │
│  │  PostgreSQL   │  │    Redis      │  │  File Storage     │     │
│  │  (all tables) │  │  (cache)      │  │  (food images)    │     │
│  └──────────────┘  └───────────────┘  └───────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## MVP vs V2 Scope

### MVP (Weeks 1-8)
- JWT auth (single user)
- Text-based food logging with Nutritionix search
- Photo food logging via GPT-4o Vision
- Fitbit integration (sleep, HRV, RHR, steps, activity)
- Wearable normalization + recovery score
- AI coaching (daily insights, food responses)
- Weekly calorie optimization
- Dashboard with macro charts and trends
- Docker Compose local deployment

### V2 (Weeks 9-12+)
- Apple Watch / HealthKit (via Terra API)
- Multi-food detection from single photo
- Behavioral pattern detector (stress-eating, weekend patterns)
- Advanced overtraining detection
- Tone personalization engine
- WhatsApp / Gmail MCP integration
- Recipe suggestions
- Multi-user support

---

## 12-Week Roadmap

| Week | Focus | Milestone | Deliverable |
|------|-------|-----------|-------------|
| 1 | Infrastructure + Docker + DB | M1 partial | Running dev environment |
| 2 | Auth E2E + API structure | M1 complete | Login/register works |
| 3 | Text food logging | M2 partial | Food search + log + macros |
| 4 | Photo food logging | M2+M3 | Photo -> AI recognition -> log |
| 5 | Fitbit OAuth2 + data pull | M4 partial | Fitbit connected + syncing |
| 6 | Normalization + dashboard | M4+M6 | Recovery score + charts |
| 7 | AI daily insights | M5 partial | Daily coaching messages |
| **8** | **Weekly optimization + integration** | **MVP** | **Usable daily driver** |
| 9 | Multi-food CV improvements | V2 | Better photo accuracy |
| 10 | Behavioral patterns + advanced AI | V2 | Pattern detection |
| 11 | HealthKit spike + observability | V2 | Sentry + structured logs |
| 12 | Security + deployment + docs | Production | Cloud-ready |

---

## Daily Execution Plan (Weeks 1-4)

### Week 1: Infrastructure

| Day | Tasks | Effort | Done When |
|-----|-------|--------|-----------|
| Mon | Create repo, folder structure, docker-compose.yml, FastAPI skeleton, Dockerfile | M+S | `docker compose up` starts services |
| Tue | SQLAlchemy async + Alembic setup, Next.js 14 + TailwindCSS + Dockerfile | M+M | DB connects, frontend loads |
| Wed | All SQLAlchemy ORM models, initial Alembic migration, Pydantic schemas | L | All tables in Postgres |
| Thu | API router structure, config management, error handling, CORS, Makefile | M | Endpoints return placeholder JSON |
| Fri | Full Docker integration test, seed data, first pytest, README | M | All services communicate |

### Week 2: Auth + Core API

| Day | Tasks | Effort | Done When |
|-----|-------|--------|-----------|
| Mon | Password hashing, JWT tokens, register/login endpoints, auth middleware | M+M | API auth works via curl |
| Tue | Auth context in Next.js, login/register pages, API client with JWT | L | Login/register in browser |
| Wed | App layout with sidebar, dashboard skeleton, user profile API | M+M | Dashboard page loads |
| Thu | Service layer pattern, response standardization, goals/targets endpoints | M | Targets can be set |
| Fri | E2E test: register -> login -> profile -> goals, bug fixes | M | Full auth flow works |

### Week 3: Text Food Logging

| Day | Tasks | Effort | Done When |
|-----|-------|--------|-----------|
| Mon | Nutritionix API client, food search endpoint, Redis caching | M+M | Food search returns results |
| Tue | Food log CRUD (create, list, update, delete), daily summary endpoint | L | All CRUD works via API |
| Wed | Food log page, food search component, add-food flow | L | Search -> select -> add works |
| Thu | Daily log list view, macro pie chart, calorie progress bar, edit/delete | L | Full food log page works |
| Fri | Recent foods quick-add, E2E test, mobile responsive, polish | M | Food logging is usable |

### Week 4: Photo Food Logging

| Day | Tasks | Effort | Done When |
|-----|-------|--------|-----------|
| Mon | Image upload endpoint, local file storage, image validation/compression | M | Images upload and save |
| Tue | GPT-4o Vision integration, prompt engineering, structured output parsing | L | Photo returns macro data |
| Wed | Backend: photo upload -> Vision -> food log creation pipeline | L | Full backend flow works |
| Thu | Frontend: photo capture, upload component, AI result display, confirm/edit | L | Photo flow works in browser |
| Fri | Edge case testing, error handling, performance check, cleanup | M | Photo logging is usable |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GPT-4o Vision accuracy <60% | Medium | High | Structured prompts + cuisine context. Fallback: text-only |
| Fitbit API rate limits/OAuth complexity | Medium | Medium | Read docs first. Daily sync, not real-time |
| Scope creep | High | High | Strict MVP scope. New ideas -> V2_IDEAS.md |
| Frontend slower than expected | Medium | Medium | Use shadcn/ui defaults. Keep UI functional, not beautiful |
| Solo dev burnout | Medium | High | Buffer Fridays. Target 6hr productive days. Weekends off |
| Nutritionix free tier limits | Low | Low | 200 calls/day is enough for solo. Fallback: USDA API |

---

## Engineering Health

### Daily Standup (5 min self-check)
```
Date: YYYY-MM-DD
Yesterday: [completed]
Today: [planned - reference task IDs]
Blockers: [anything stuck]
Confidence: [Green/Yellow/Red]
```

### Weekly Review (30 min, every Friday)
- Tasks completed vs planned
- Scope changes
- What went well / what to improve
- Next week adjustments

### Scope Containment
1. New feature idea? -> V2_IDEAS.md, no discussion
2. Task taking 2x estimated effort? -> Stop, reassess
3. Friday scope audit: anything crept in?
4. "Ship Ugly" principle: functional > beautiful for MVP
