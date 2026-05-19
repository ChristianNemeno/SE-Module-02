# ReadRight API Contract

> Version 1.0 · Reference for all team members

## POST /analyze

| | |
|---|---|
| **URL** | `POST /analyze` |
| **Auth** | `X-API-Key: <static key>` (header) |
| **Content-Type** | `multipart/form-data` |

### Request Fields

| Field | Type | Description |
|---|---|---|
| `file` | binary | Video file (`video/webm` or `video/mp4`) |
| `passage_id` | string | Phil-IRI passage identifier |

### Responses

**200 OK**
```json
{
  "wpm": 85.5,
  "word_recognition_pct": 92.3,
  "reading_level": "Instructional",
  "miscues": {
    "correct": 48, "mispronunciation": 2, "substitution": 1,
    "omission": 1, "insertion": 0, "repetition": 1, "refusal_to_pronounce": 0
  },
  "behaviors": {
    "finger_pointing": false, "loss_of_place": false,
    "monotone_reading": false, "word_by_word_reading": false, "inaudible_reading": false
  }
}
```

**401 Unauthorized** — Invalid or missing `X-API-Key`

**500 Internal Server Error**
```json
{ "error": "...", "code": "PIPELINE_FAILED" | "DB_WRITE_FAILED" }
```

---

## Supabase: `sessions` Table

### INSERT (after assessment)

All 19 fields. Key fields:
- `learner_id` — from JWT `sub`
- `passage_id` — from frontend request
- `session_timestamp` — `now()`

### SELECT (history view)

```sql
SELECT * FROM sessions
WHERE learner_id = auth.uid()
ORDER BY session_timestamp ASC;
```

---

## Environment Variables

### Frontend (Vite)

| Variable | Description |
|---|---|
| `VITE_SUPABASE_URL` | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `VITE_FASTAPI_URL` | FastAPI base URL |
| `VITE_API_KEY` | Static API key for X-API-Key header |

### FastAPI Backend

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (never expose to frontend) |
| `API_KEY` | Static key validated on every `/analyze` request |
