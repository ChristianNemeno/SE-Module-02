---
name: solid-oop
description: >
  Enforce SOLID principles and class-based OOP patterns in this Python/FastAPI project.
  Use this skill whenever writing new classes, services, routers, or pipelines; when
  reviewing code for SOLID violations; when adding a new feature that touches the
  GO2/GO3 service layer; when wiring up FastAPI routes; or when the user asks about
  architecture, design patterns, dependency injection, interfaces, or abstractions.
  Trigger on: "add a service", "create a class", "wire up the router", "how should I
  structure this", "dependency injection", "OOP", "SOLID", "refactor this", or any time
  you are about to write a plain function where a class clearly belongs.
  This project deliberately avoids the standard FastAPI functional style — always use
  class-based controllers, service objects, and Protocol interfaces instead.
---

# SOLID OOP Coding Standard — ReadRight FastAPI Microservice

This project uses **class-based OOP throughout** — no bare route functions, no
module-level business logic. Every component has a class with a single job, injected
via FastAPI's `Depends()`. Follow these principles and patterns for all new code.

---

## The Five Principles — Applied

### S — Single Responsibility
One class, one reason to change.

- **Controllers** handle HTTP only: auth check, file I/O, calling the service, returning
  the response. They know nothing about Phil-IRI rules.
- **Services** orchestrate pipelines. They know the order of operations but not how each
  step works.
- **Pipeline classes** (Transcriber, MiscueClassifier, ScoringEngine) do one computation
  each. They know nothing about HTTP or Supabase.
- **Repositories** talk to Supabase. They know nothing about scoring logic.

If you find yourself thinking "this class does X *and* Y" — split it.

### O — Open/Closed
Add new behaviour by adding new classes, not by editing existing ones.

Use `Protocol` to define the contract. New pipeline variants (e.g. a GPU transcriber,
a stricter classifier) implement the protocol — existing code that depends on the
protocol never changes.

```python
from typing import Protocol

class TranscriberProtocol(Protocol):
    def transcribe(self, wav_path: str) -> list[WordSegment]: ...

# WhisperX implementation — today
class WhisperXTranscriber:
    def transcribe(self, wav_path: str) -> list[WordSegment]: ...

# Future GPU implementation — tomorrow, no edits needed upstream
class WhisperXGPUTranscriber:
    def transcribe(self, wav_path: str) -> list[WordSegment]: ...
```

### L — Liskov Substitution
Any class that satisfies a Protocol must be fully substitutable.

If `ScoringEngine` depends on `TranscriberProtocol`, swapping
`WhisperXTranscriber` for `WhisperXGPUTranscriber` must produce identical
output shapes — same `list[WordSegment]`, same field names, same semantics.
Never let a subtype silently change behaviour (e.g. returning fewer fields,
changing units).

### I — Interface Segregation
Prefer narrow, specific protocols over one fat interface.

```python
# Good — each protocol is minimal and focused
class TranscriberProtocol(Protocol):
    def transcribe(self, wav_path: str) -> list[WordSegment]: ...

class ClassifierProtocol(Protocol):
    def classify(self, words: list[WordSegment], passage: str) -> MiscueCounts: ...

class ScorerProtocol(Protocol):
    def score(self, words: list[WordSegment], counts: MiscueCounts) -> ScoreResult: ...

# Bad — one interface for everything
class GO2Protocol(Protocol):
    def transcribe(...): ...
    def classify(...): ...
    def score(...): ...
```

A service that only needs to score should only depend on `ScorerProtocol`, not a
bloated interface that drags in transcription methods it never calls.

### D — Dependency Inversion
Depend on abstractions (Protocols), never on concrete classes.

Wire concrete classes in one place — the FastAPI dependency providers — and
inject abstractions everywhere else.

```python
# The service depends on protocols, not implementations
class GO2Service:
    def __init__(
        self,
        transcriber: TranscriberProtocol,
        classifier: ClassifierProtocol,
        scorer: ScorerProtocol,
    ) -> None:
        self._transcriber = transcriber
        self._classifier = classifier
        self._scorer = scorer
```

---

## FastAPI OOP Pattern — Class-Based Controllers

**Never** write bare `@router.post(...)` functions. Route handlers live as methods
on a controller class. The controller's only job is HTTP: auth, I/O, delegation,
response.

```python
# app/routers/analyze.py
from fastapi import APIRouter, Depends, Form, Header, HTTPException, UploadFile
from app.models.assessment import AssessmentResult
from app.services.analyze_service import AnalyzeService
from app.dependencies import get_analyze_service

class AnalyzeController:
    def __init__(self) -> None:
        self.router = APIRouter(prefix="", tags=["analyze"])
        self.router.add_api_route(
            "/analyze",
            self.analyze,
            methods=["POST"],
            response_model=AssessmentResult,
        )
        self.router.add_api_route("/health", self.health, methods=["GET"])

    async def analyze(
        self,
        file: UploadFile,
        passage_id: str = Form(...),
        x_api_key: str = Header(...),
        service: AnalyzeService = Depends(get_analyze_service),
    ) -> AssessmentResult:
        self._check_api_key(x_api_key)
        return await service.run(file, passage_id)

    async def health(self) -> dict[str, str]:
        return {"status": "ok"}

    def _check_api_key(self, key: str) -> None:
        from app.config import settings
        if key != settings.API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")

# Register in app/main.py:
# controller = AnalyzeController()
# app.include_router(controller.router)
```

---

## Service Layer Pattern

Services orchestrate pipelines. They do not contain business logic themselves —
they call the right components in the right order.

```python
# app/services/analyze_service.py
import asyncio
from pathlib import Path
from uuid import uuid4

from app.services.go2.go2_pipeline import GO2Pipeline
from app.services.go3.go3_pipeline import GO3Pipeline
from app.utils.result_consolidator import ResultConsolidator
from app.utils.ffmpeg import extract_audio, normalize_video
from app.repositories.session_repository import SessionRepository
from app.models.assessment import AssessmentResult

class AnalyzeService:
    def __init__(
        self,
        go2: GO2Pipeline,
        go3: GO3Pipeline,
        consolidator: ResultConsolidator,
        sessions: SessionRepository,
    ) -> None:
        self._go2 = go2
        self._go3 = go3
        self._consolidator = consolidator
        self._sessions = sessions

    async def run(self, file: UploadFile, passage_id: str) -> AssessmentResult:
        tmp_path = Path(f"/tmp/{uuid4()}{Path(file.filename).suffix}")
        tmp_path.write_bytes(await file.read())
        wav_path = extract_audio(tmp_path)
        mp4_path = normalize_video(tmp_path)
        try:
            go2_result, go3_result = await asyncio.gather(
                self._go2.run(wav_path, passage_id),
                self._go3.run(mp4_path, wav_path),
            )
            result = self._consolidator.merge(go2_result, go3_result)
            await self._sessions.insert(result, passage_id)
            return result
        finally:
            for p in [tmp_path, wav_path, mp4_path]:
                p.unlink(missing_ok=True)
```

---

## Pipeline Pattern (GO2 / GO3)

Each pipeline is a class that composes smaller single-responsibility classes.
The pipeline's job is sequencing — not implementing any step itself.

```python
# app/services/go2/go2_pipeline.py
from app.services.go2.transcriber import TranscriberProtocol
from app.services.go2.miscue_classifier import ClassifierProtocol
from app.services.go2.scoring_engine import ScorerProtocol
from app.models.assessment import GO2Result

class GO2Pipeline:
    def __init__(
        self,
        transcriber: TranscriberProtocol,
        classifier: ClassifierProtocol,
        scorer: ScorerProtocol,
    ) -> None:
        self._transcriber = transcriber
        self._classifier = classifier
        self._scorer = scorer

    async def run(self, wav_path: Path, passage_id: str) -> GO2Result:
        passage = await self._fetch_passage(passage_id)
        words = self._transcriber.transcribe(str(wav_path))
        counts = self._classifier.classify(words, passage)
        return self._scorer.score(words, counts)
```

---

## Dependency Wiring (Single Place)

All concrete class instantiation happens in `app/dependencies.py`. The rest of
the codebase only sees protocols and abstract types.

```python
# app/dependencies.py
from functools import lru_cache
from app.services.go2.transcriber import WhisperXTranscriber
from app.services.go2.miscue_classifier import MiscueClassifier
from app.services.go2.scoring_engine import ScoringEngine
from app.services.go2.go2_pipeline import GO2Pipeline
from app.services.analyze_service import AnalyzeService
from app.repositories.session_repository import SupabaseSessionRepository

@lru_cache
def get_go2_pipeline() -> GO2Pipeline:
    return GO2Pipeline(
        transcriber=WhisperXTranscriber(),
        classifier=MiscueClassifier(),
        scorer=ScoringEngine(),
    )

def get_analyze_service(
    go2: GO2Pipeline = Depends(get_go2_pipeline),
    ...
) -> AnalyzeService:
    return AnalyzeService(go2=go2, ...)
```

---

## Repository Pattern

Database access lives in repository classes. Services call repositories;
repositories call Supabase. No service ever imports `supabase` directly.

```python
# app/repositories/session_repository.py
from typing import Protocol
from app.models.assessment import AssessmentResult

class SessionRepositoryProtocol(Protocol):
    async def insert(self, result: AssessmentResult, passage_id: str) -> None: ...

class SupabaseSessionRepository:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def insert(self, result: AssessmentResult, passage_id: str) -> None:
        self._client.table("sessions").insert(
            {**result.model_dump(), "passage_id": passage_id}
        ).execute()
```

---

## Red Flags — Stop and Refactor

| You see this | Fix |
|---|---|
| Business logic inside a route handler method | Move to a service class |
| `import supabase` outside `repositories/` | Move DB call into a repository |
| A class with methods that don't share state | Might be a free function — or split into two classes |
| Concrete class imported in a service (`from .transcriber import WhisperXTranscriber`) | Depend on the Protocol; wire the concrete in `dependencies.py` |
| A Protocol with >4 methods | Split into focused smaller protocols |
| `@staticmethod` doing real work | Probably its own class |
| One class handling both GO2 and GO3 | SRP violation — one pipeline per domain |

---

## Folder Contract

```
app/
  routers/          # Controllers only — HTTP in, result out
  services/
    analyze_service.py   # Orchestrates GO2 + GO3
    go2/            # TranscriberProtocol, WhisperXTranscriber, MiscueClassifier, ScoringEngine, GO2Pipeline
    go3/            # GO3Pipeline and its components
  repositories/     # Supabase access only
  models/           # Pydantic models and TypedDicts — no logic
  utils/            # Stateless helpers (ffmpeg wrappers, result consolidator)
  dependencies.py   # ONLY place that instantiates concrete classes
  config.py         # Settings (pydantic-settings BaseSettings)
  main.py           # App factory, CORS, startup hook, router registration
```
