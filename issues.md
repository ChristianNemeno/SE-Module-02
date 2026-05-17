RR-004 · Scaffold FastAPI Microservice Repo with Stub /analyze

Summary

Bootstrap the FastAPI Python microservice repo with all AI dependencies, folder structure, a working stub /analyze endpoint, and a local dev server. The stub enables frontend development to proceed without waiting for real AI pipelines.

Suggested Role: @ai-dev | Day: 1 AM | Effort: S (2–3 hrs)

requirements.txt

fastapi
uvicorn[standard]
python-multipart
whisperx
mediapipe
librosa
praat-parselmouth
ffmpeg-python
supabase
python-dotenv
pydantic

Folder Structure

app/
  main.py              # FastAPI app, CORS, startup events
  routers/
    analyze.py         # POST /analyze handler
  services/
    go2/               # Transcriber, MiscueClassifier, ScoringEngine
    go3/               # CVDetector, ProsodyAmplitudeDetector
  models/
    assessment.py      # AssessmentResultJSON Pydantic model
  utils/
    result_consolidator.py

Stub Response (implement first — unblocks frontend)

@router.post("/analyze")
async def analyze(file: UploadFile, passage_id: str = Form(...), x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401)
    return {"wpm": 85.5, "word_recognition_pct": 92.3, "reading_level": "Instructional",
            "miscues": {"correct": 48, "mispronunciation": 2, ...},
            "behaviors": {"finger_pointing": False, ...}}

Also implement GET /health and CORS for localhost:5173.

Definition of Done

uvicorn app.main:app --reload runs without errors

POST /analyze with any video file returns stub JSON (200)

Wrong X-API-Key returns 401

AssessmentResultJSON typed as Pydantic BaseModel

CORS configured for frontend origin

RR-023 · WPM + Scoring + Reading Level

Summary

Compute WPM, word recognition %, and Phil-IRI reading level from miscue data + timestamps. Short task — pure arithmetic.

Suggested Role: @ai-dev | Day: 2 AM | Effort: S (2–3 hrs)

Phil-IRI Formulas (non-negotiable — deviation invalidates the system)

# WPM
wpm = total_passage_words / (last_word_end - first_word_start) * 60

# Word Recognition %
# Error miscues: mispronunciation + substitution + omission + refusal_to_pronounce
# NOT insertion or repetition (per Phil-IRI standard)
error_count = counts['mispronunciation'] + counts['substitution'] + counts['omission'] + counts['refusal_to_pronounce']
word_recognition_pct = (total_words - error_count) / total_words * 100

# Reading Level Classification
if word_recognition_pct >= 97:
    reading_level = "Independent"
elif word_recognition_pct >= 91:
    reading_level = "Instructional"
else:
    reading_level = "Frustration"

Unit Tests (include these exactly)

100 words read in 90 seconds → WPM = 66.7

3 errors in 50 words → 94% → "Instructional"

7 errors in 50 words → 86% → "Frustration"

0 errors in 52 words → 100% → "Independent"

reading_level is always exactly one of: "Frustration", "Instructional", "Independent"

Definition of Done

All 4 unit tests pass

Output dict matches AssessmentResultJSON GO2 fields exactly

reading_level is one of the 3 exact strings above (no other values)

RR-022 · Phil-IRI Miscue Classifier

Summary

Rule-based classifier that maps aligned transcript words to Phil-IRI's 7 miscue categories.

Suggested Role: @ai-dev | Day: 2 AM | Effort: M (4–5 hrs)

Phil-IRI Miscue Taxonomy

Category

Definition

correct

Word matches passage (edit distance ≤ 1)

mispronunciation

Phonetically similar deviation (edit distance 2–3)

substitution

Completely different word at same position

omission

Passage word absent from transcript

insertion

Extra transcript word not in passage

repetition

Same word appears consecutively in transcript

refusal_to_pronounce

Passage word with no clear transcription and score < 0.3

Implementation

# app/services/go2/miscue_classifier.py
from difflib import SequenceMatcher

class MiscueClassifier:
    def classify(self, transcript_words: list[dict], passage_text: str) -> dict:
        passage_tokens = self._tokenize(passage_text)
        # Use SequenceMatcher to align transcript words to passage words
        # Classify each opcode: equal→correct, replace→mispron/sub, delete→omission, insert→insertion
        counts = {k: 0 for k in ['correct','mispronunciation','substitution','omission','insertion','repetition','refusal_to_pronounce']}
        # ... classification logic
        return counts
  
    def _tokenize(self, text: str) -> list[str]:
        import re
        return [w.lower() for w in re.findall(r"[a-zA-Z']+", text)]

Unit Test Cases

100-word passage, perfect reading → correct=100, all others=0

"the" substituted with "a" → substitution+=1

Word completely missing → omission+=1

Extra word inserted → insertion+=1

Definition of Done

Unit test: known transcript vs passage returns expected counts

All 7 miscue categories populated (0 for absent types)

Handles empty transcript (all words become omissions)

Handles extra words at end gracefully


RR-020 · FastAPI /analyze Real Orchestrator

Summary

Replace the stub handler with a real async orchestrator. Runs GO2 + GO3 pipelines in parallel via asyncio.gather(), writes results to Supabase, deletes temp files.

Suggested Role: @ai-dev | Day: 2 PM | Effort: M (4 hrs)

Implementation

@router.post("/analyze")
async def analyze(file: UploadFile, passage_id: str = Form(...), x_api_key: str = Header(...)):
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401)
  
    # Save uploaded file to temp dir
    tmp_path = f"/tmp/{uuid4()}{Path(file.filename).suffix}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
  
    try:
        # FFmpeg extraction
        wav_path = extract_audio(tmp_path)   # ffmpeg -i input -vn -acodec pcm_s16le -ar 16000 -ac 1
        mp4_path = normalize_video(tmp_path) # ffmpeg -i input -vcodec copy -acodec aac
      
        # Parallel GO2 + GO3 execution
        go2_result, go3_result = await asyncio.gather(
            run_go2_pipeline(wav_path, passage_id),
            run_go3_pipeline(mp4_path, wav_path)
        )
      
        # Merge results
        result = ResultConsolidator.merge(go2_result, go3_result)
      
        # Write to Supabase (service key — not learner JWT)
        supabase.table("sessions").insert({**result, "passage_id": passage_id}).execute()
      
        return result
    finally:
        # Always delete temp files
        for p in [tmp_path, wav_path, mp4_path]:
            Path(p).unlink(missing_ok=True)

Definition of Done

Accepts webm (Chrome Android) and mp4 (iOS Safari)

FFmpeg extracts WAV and normalized video without errors

GO2 + GO3 run in parallel (asyncio.gather)

Temp files deleted after processing (verified via filesystem check)

Supabase INSERT writes complete record

Returns 500 with error code if either pipeline fails

RR-021 · Implement WhisperX ASR + Forced Alignment

Summary

The most compute-intensive task. WhisperX model must be loaded ONCE at startup (not per request). Word-level forced alignment is essential for WPM and miscue classification.

Suggested Role: @ai-dev | Day: 1–2 | Effort: L (6–8 hrs) | Risk: HIGH + EXTERNAL

Implementation

# app/services/go2/transcriber.py

import whisperx

# Load ONCE at startup — pre-warm to avoid cold-start latency
_model = None
_align_model = None
_metadata = None

def load_models():
    global _model, _align_model, _metadata
    _model = whisperx.load_model("base", device="cpu", language="en")
    _align_model, _metadata = whisperx.load_align_model(language_code="en", device="cpu")

class Transcriber:
    def transcribe(self, wav_path: str, passage_text: str) -> list[dict]:
        result = _model.transcribe(wav_path, batch_size=4)
        aligned = whisperx.align(result["segments"], _align_model, _metadata, wav_path, device="cpu")
        # Returns: [{"word": str, "start": float, "end": float, "score": float}, ...]
        words = []
        for seg in aligned.get("word_segments", []):
            words.append({"word": seg["word"].lower().strip(), "start": seg["start"], "end": seg["end"], "score": seg.get("score", 1.0)})
        return words

Startup Hook (app/main.py)

@app.on_event("startup")
async def startup_event():
    load_models()  # Pre-warm — first request won't pay cold-start cost

Performance Expectations

Model loading: 30–60s (once at startup)

Inference on 2-min WAV: 30–90s on CPU

Document actual timing in a comment on this issue after first test run

Definition of Done

Given a real WAV file → returns word list with timestamps

Model loaded at startup, NOT per request

Handles silence gaps without crashing

Returns at least word, start, end per token

Processes 2-min WAV in under 90s on CPU