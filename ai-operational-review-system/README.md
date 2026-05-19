# AI Operational Review System

An AI-powered weekly diagnostic tool that analyses how you allocate time, execute priorities, and make decisions. Produces McKinsey-style operational reviews — not motivational coaching.

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# Optional: set your Anthropic API key for real AI reviews
# Without it, a mock review is returned so the app still works
export ANTHROPIC_API_KEY=sk-ant-...

# Seed the database with 2 weeks of test data
python seed_data.py

# Start the backend
python app.py
```

Backend runs at `http://localhost:5000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### 3. Environment variables

Copy `.env.example` to `.env` in the backend directory:

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | No | — | Claude API key. If absent, mock reviews are returned. |
| `DB_PATH` | No | `operational_review.db` | Path to the SQLite database file. |
| `PORT` | No | `5000` | Backend port. |
| `VITE_API_URL` | No | `http://localhost:5000` | Frontend: backend URL override. |

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

22 unit tests covering all 6 metrics and 5 failure patterns.

## Project Structure

```
ai-operational-review-system/
  backend/
    app.py               Flask API — all endpoints
    database.py          SQLite initialisation
    metrics.py           6 metric calculations
    pattern_detection.py 6 failure pattern detectors
    prompt_builder.py    Constructs the AI review prompt
    llm_service.py       Anthropic Claude API integration + mock fallback
    seed_data.py         2 weeks of realistic test data
    requirements.txt
    tests/
      test_metrics.py
      test_patterns.py
  frontend/
    src/
      App.jsx                      Main app shell + navigation
      components/
        OnboardingForm.jsx         One-time calibration form
        DailyInputForm.jsx         Daily telemetry log
        MondayWeeklyForm.jsx       Monday commitments
        FridayWeeklyReviewForm.jsx Friday outcomes + triggers AI review
        MetricsDashboard.jsx       6-metric grid
        AIWeeklyReview.jsx         Diagnosis / Evidence / Intervention display
        ReviewHistory.jsx          Collapsible past reviews
      api/
        client.js                  Typed API wrapper
  .env.example
  README.md
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/onboarding` | Submit onboarding profile |
| GET | `/api/onboarding` | Get current profile |
| POST | `/api/daily-log` | Submit daily log + tasks |
| GET | `/api/daily-logs` | Get recent logs |
| POST | `/api/weekly/monday` | Submit Monday commitments |
| GET | `/api/weekly/monday` | Get Monday inputs |
| POST | `/api/weekly/friday` | Submit Friday review |
| GET | `/api/weekly/friday` | Get Friday reviews |
| GET | `/api/metrics/current-week` | Calculate week metrics |
| GET | `/api/dashboard` | Full dashboard data |
| POST | `/api/reviews/generate` | Generate AI weekly review |
| GET | `/api/reviews` | Review history |

## How the AI Review Works

1. Friday form submission → `POST /api/weekly/friday`
2. Frontend calls `POST /api/reviews/generate`
3. Backend calculates all 6 metrics and runs 6 pattern detectors
4. `prompt_builder.py` assembles a structured prompt with metrics, patterns, and onboarding context
5. `llm_service.py` calls Claude (or returns a mock if no API key)
6. Review is stored in SQLite and returned to the frontend
7. Dashboard shows Diagnosis → Evidence → Intervention

## The 6 Failure Patterns

| Pattern | Detection logic |
|---|---|
| Planning Inflation | ≥5 planned tasks + planning accuracy <50% |
| False Priority | ≥2 priorities incomplete + low PCR or low deep work |
| Reactive Capture | Reactive hours > deep work + reactive >8h + PCR <50% |
| Decision Deferral | Repeated keywords in deferred tasks + deferral rate >30% |
| Leverage Leakage | Low-leverage + admin hours > deep work + total >8h |
| Depth Deprivation | Average deep work blocks/day <1.0 over ≥3 data points |

Pattern maturity is labelled: *Early signal* / *Emerging pattern* / *Confirmed pattern*.
