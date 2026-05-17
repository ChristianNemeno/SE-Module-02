---
name: python-strong-types
description: >
  Enforce and implement strong typing in Python 3.12 code using pyright.
  Use this skill whenever the user wants to: add type annotations, fix pyright/mypy
  errors, convert untyped Python to fully typed, upgrade old typing imports (Optional,
  Union, List, Dict) to modern syntax, convert plain classes to dataclasses or Pydantic
  models, create TypedDict for dict shapes, review code for missing types, or make a
  Python file pass pyright strict mode. Trigger on phrases like "add types", "type this",
  "fix pyright errors", "make this strongly typed", "annotate this function", "this has
  Any everywhere", or whenever you see untyped Python code that should be typed.
---

# Python Strong Types (Python 3.12 + Pyright)

You are helping the user write Python code that is **fully, correctly typed** under
`pyright` in strict mode. The goal is real type safety — catching bugs at edit time,
not at runtime.

## Core Workflow

1. **Read the file(s)** the user pointed at (or the current open file)
2. **Run pyright** on them to get a baseline of current errors
3. **Identify all typing gaps** (see checklist below)
4. **Fix everything** — apply all transformations in one pass per file
5. **Run pyright again** to confirm zero errors remain
6. Report what changed

If `mcp__ide__getDiagnostics` is available, use it in addition to (or instead of) the
pyright CLI — it gives line-accurate diagnostics from the language server.

## Running Pyright

```bash
pyright <file_or_dir>              # check a file or directory
pyright --outputjson <file>        # machine-readable output
pyright --verifytypes <package>    # for library authors
```

To enable strict mode in a project, add `pyrightconfig.json`:
```json
{ "typeCheckingMode": "strict" }
```

Or add inline per-file: `# pyright: strict` at the top of the file.

## Python 3.12 Type Syntax — What to Use

Always use the **modern built-in** forms. Never import from `typing` when the built-in
works (Python 3.9+ for generics, 3.10+ for `|`).

| Old (don't write this)           | Modern 3.12 form              |
|----------------------------------|-------------------------------|
| `Optional[X]`                    | `X \| None`                   |
| `Union[X, Y]`                    | `X \| Y`                      |
| `List[X]`                        | `list[X]`                     |
| `Dict[K, V]`                     | `dict[K, V]`                  |
| `Tuple[X, Y]`                    | `tuple[X, Y]`                 |
| `Set[X]`                         | `set[X]`                      |
| `FrozenSet[X]`                   | `frozenset[X]`                |
| `Type[X]`                        | `type[X]`                     |
| `Callable[[A, B], R]`            | `Callable[[A, B], R]` (still from `typing`) |
| `TypeAlias = ...`                | `type Alias = ...` (PEP 695)  |
| `TypeVar("T")`                   | `type T = TypeVar("T")` or keep old form |

Still import from `typing` when needed: `Callable`, `ClassVar`, `Final`, `Literal`,
`Protocol`, `TypeVar`, `ParamSpec`, `Self`, `TypeGuard`, `Annotated`, `overload`,
`cast`, `TYPE_CHECKING`.

## Typing Gap Checklist

Work through these in order for every function, class, and module-level variable:

### Functions
- [ ] Every parameter has a type annotation (except `self`/`cls`)
- [ ] Every function has a `-> ReturnType` annotation
- [ ] `-> None` on functions that don't return a value (not just omitted)
- [ ] No bare `*args` or `**kwargs` — type them: `*args: str`, `**kwargs: int`
- [ ] Async functions annotated: `async def foo() -> Awaitable[X]` or just `-> X`

### Variables & Attributes
- [ ] Module-level variables that pyright can't infer are annotated: `x: int = 0`
- [ ] Class attributes declared in `__init__` or class body with types
- [ ] `ClassVar[X]` for class-level attributes (not instance attrs)
- [ ] `Final[X]` for constants that should never be reassigned

### Collections
- [ ] No bare `list`, `dict`, `set`, `tuple` — always parameterized: `list[str]`
- [ ] No bare `dict` as a catch-all — use `TypedDict` or `dict[str, Any]` + a comment

### Special patterns
- [ ] `__init__` always returns `None` explicitly
- [ ] Properties annotated on the getter (setter/deleter inherit)
- [ ] `@classmethod` first param typed as `type[Self]` or `type[ClassName]`
- [ ] `@staticmethod` no implicit params
- [ ] Exception variables: `except ValueError as e:` — `e` is already typed by Python

## When to Use Each Construct

Choose the right container for the job — wrong choice leads to fighting the type system.

### `@dataclass` — pure data, no validation
Use when the object holds data, no business logic, no external input:
```python
from dataclasses import dataclass, field

@dataclass
class WordAlignment:
    word: str
    start: float
    end: float
    score: float = 1.0
    alternatives: list[str] = field(default_factory=list)
```

### `Pydantic BaseModel` — API boundaries, validated input
Use for anything that crosses a system boundary: HTTP requests/responses, Supabase
rows, file payloads. Pydantic validates at runtime AND pyright understands the types:
```python
from pydantic import BaseModel, Field

class AssessmentResult(BaseModel):
    wpm: float
    word_recognition_pct: float = Field(ge=0, le=100)
    reading_level: Literal["Frustration", "Instructional", "Independent"]
    correct: int
    mispronunciation: int
    substitution: int
    omission: int
    insertion: int
    repetition: int
    refusal_to_pronounce: int
```

### `TypedDict` — typed dict shapes (e.g., config, JSON blobs)
Use when you're working with a plain dict that has a known structure but you don't
control its construction (e.g., it comes from JSON, a third-party library, kwargs):
```python
from typing import TypedDict

class WordSegment(TypedDict):
    word: str
    start: float
    end: float
    score: float
```

### `Protocol` — structural subtyping (duck typing with types)
Use instead of ABCs when you want "anything that has these methods":
```python
from typing import Protocol

class Transcribable(Protocol):
    def transcribe(self, wav_path: str) -> list[WordSegment]: ...
```

### `Literal` — restrict to a fixed set of values
```python
from typing import Literal

ReadingLevel = Literal["Frustration", "Instructional", "Independent"]
MiscueCategory = Literal[
    "correct", "mispronunciation", "substitution",
    "omission", "insertion", "repetition", "refusal_to_pronounce"
]
```

### `type` alias (PEP 695) — named type shortcuts
```python
type MiscueCounts = dict[MiscueCategory, int]
type WordList = list[WordSegment]
```

## Handling `Any`

`Any` is an escape hatch that disables type checking for that value. It's sometimes
necessary (interop with untyped libraries), but treat every `Any` as a code smell:

- **Third-party library with no stubs**: use `Any` at the call site and wrap in a typed
  function so `Any` doesn't leak into your own code
- **JSON blobs**: type as `dict[str, Any]` at the boundary, then validate with Pydantic
  and work with typed models inside
- **`cast()`**: use when you know more than pyright does, but document why

```python
from typing import Any, cast

# OK: isolate Any at the JSON boundary
raw: dict[str, Any] = response.json()
result = AssessmentResult.model_validate(raw)  # now fully typed
```

## FastAPI-Specific Patterns

Since this project uses FastAPI:

```python
from fastapi import FastAPI, UploadFile, Form, Header, HTTPException
from fastapi.responses import JSONResponse

# Request body — use Pydantic models
# FastAPI generates OpenAPI schema from them automatically

# Form fields typed explicitly
@router.post("/analyze")
async def analyze(
    file: UploadFile,
    passage_id: str = Form(...),
    x_api_key: str = Header(...),
) -> AssessmentResult:  # <- type the return, FastAPI uses it for schema
    ...
```

Always annotate the return type of route handlers — FastAPI + pyright will catch
mismatches between what you return and what the schema says.

## Common Pyright Error Fixes

| Pyright error | Fix |
|---|---|
| `"X" is not a known attribute of "Y"` | Add the attribute to the class or use `hasattr` guard |
| `Return type "X" is not assignable to return type "Y"` | Fix the return annotation or the return value |
| `Argument of type "X \| None" cannot be assigned to "X"` | Add a `None` check before the call |
| `Cannot access member "X" for type "None"` | Guard with `if obj is not None:` or use `assert obj is not None` |
| `Type of "X" is unknown` | Annotate the variable explicitly |
| `"list[Unknown]" is not assignable to "list[str]"` | Initialize with a typed annotation: `items: list[str] = []` |
| `Operator "\|" not supported for types "X" and "Y"` | You're on Python < 3.10 syntax; add `from __future__ import annotations` |

## Narrowing — Letting Pyright Understand Your Logic

Pyright tracks what type a variable *could* be at each point in the code. Help it narrow:

```python
def process(value: str | None) -> str:
    if value is None:
        return ""
    # here pyright knows value is str, not str | None
    return value.upper()

# isinstance narrowing
def display(x: int | str) -> str:
    if isinstance(x, int):
        return str(x)   # x is int here
    return x.upper()    # x is str here

# TypeGuard for custom narrowing
from typing import TypeGuard

def is_word_segment(d: dict[str, object]) -> TypeGuard[WordSegment]:
    return "word" in d and "start" in d and "end" in d
```

## Output Format

When you finish typing a file, report:
1. **Pyright before**: error count
2. **Changes made**: bullet list of what was added/converted (e.g., "12 function signatures annotated", "MiscueCounts dict → TypedDict", "3 Optional[X] → X | None")
3. **Pyright after**: error count (target: 0)
4. If errors remain: show them and explain why (e.g., untyped third-party library)
