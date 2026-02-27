from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .composition import build_composition_document, composition_to_runtime, load_composition, save_composition
from .logic_export import create_logic_project_bundle
from .midi_pack import generate_midi_pack
from .pipeline import analyze_melody_data, load_input_file


class ArrangeRequest(BaseModel):
    composition: dict[str, Any] | None = None
    composition_path: str | None = None
    project_name: str = Field(default="Studio Arrangement")
    output_dir: str = Field(default="studio_outputs/logic_exports")
    quantize_subdivisions: int = Field(default=4, ge=1, le=32)
    complexity: str = Field(default="rich")
    arrangement_bars: int | None = Field(default=32, ge=1, le=512)
    loop_melody: bool = True


class MidiPackRequest(BaseModel):
    composition: dict[str, Any] | None = None
    composition_path: str | None = None
    output_dir: str = Field(default="studio_outputs/midi_packs")
    project_prefix: str = Field(default="Studio Pack")
    styles: list[str] = Field(default_factory=lambda: ["pop", "modal", "jazz"])
    bars: list[int] = Field(default_factory=lambda: [32, 64])
    complexity: str = Field(default="rich")


def _ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def _now_stamp() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")


def _load_runtime_from_request(composition: dict[str, Any] | None, composition_path: str | None):
    if composition is not None:
        return composition_to_runtime(composition)
    if composition_path:
        payload = load_composition(composition_path)
        return composition_to_runtime(payload)
    raise HTTPException(status_code=400, detail="composition or composition_path is required")


app = FastAPI(title="Melody Architect Studio API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/digitize")
async def digitize(
    file: UploadFile = File(...),
    style: str = Form(default="pop"),
    bars: int | None = Form(default=None),
    tempo: float | None = Form(default=None),
    beats_per_bar: int = Form(default=4),
    mode: str | None = Form(default=None),
) -> JSONResponse:
    suffix = Path(file.filename or "input").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        raw = await file.read()
        tmp.write(raw)
        tmp_path = Path(tmp.name)

    try:
        data = load_input_file(tmp_path, tempo_override=tempo, beats_per_bar=beats_per_bar)
        report = analyze_melody_data(data=data, style=style, bars=bars, forced_mode=mode, top_k=5)
        composition = build_composition_document(data, report)

        out_dir = _ensure_dir("studio_outputs/compositions")
        out_path = out_dir / f"{_now_stamp()}_{Path(file.filename or 'input').stem}.composition.json"
        save_composition(out_path, composition)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass

    return JSONResponse(
        {
            "ok": True,
            "composition_path": str(out_path),
            "summary": {
                "key": f"{report['key_estimate']['tonic']} {report['key_estimate']['mode']}",
                "candidate": report["harmony"]["selected_candidate"]["name"],
                "validation": report["validation"]["passed"],
            },
            "composition": composition,
        }
    )


@app.post("/api/arrange")
def arrange(request: ArrangeRequest) -> JSONResponse:
    data, report = _load_runtime_from_request(request.composition, request.composition_path)
    try:
        bundle = create_logic_project_bundle(
            data=data,
            report=report,
            output_dir=request.output_dir,
            project_name=request.project_name,
            quantize_subdivisions=request.quantize_subdivisions,
            complexity=request.complexity,
            arrangement_bars=request.arrangement_bars,
            loop_melody=request.loop_melody,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JSONResponse({"ok": True, "bundle": bundle})


@app.post("/api/midi-pack")
def midi_pack(request: MidiPackRequest) -> JSONResponse:
    data, _report = _load_runtime_from_request(request.composition, request.composition_path)
    # Persist a temporary composition-based source and run pack generation via runtime info.
    tmp_dir = _ensure_dir("studio_outputs/midi_pack_runtime")
    temp_input = tmp_dir / f"{_now_stamp()}_runtime.csv"
    rows = ["pitch,start,end,velocity\n"]
    for note in data.sorted_notes():
        rows.append(f"{note.pitch},{note.start:.6f},{note.end:.6f},{note.velocity}\n")
    temp_input.write_text("".join(rows), encoding="utf-8")

    try:
        bundles = generate_midi_pack(
            input_path=temp_input,
            output_dir=request.output_dir,
            project_prefix=request.project_prefix,
            styles=tuple(request.styles),
            arrangement_bars=tuple(request.bars),
            tempo_override=data.tempo_bpm,
            beats_per_bar=data.beats_per_bar,
            complexity=request.complexity,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return JSONResponse({"ok": True, "bundle_count": len(bundles), "bundles": bundles})


def create_app() -> FastAPI:
    frontend_dir = Path(__file__).parent / "frontend"
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    return app


create_app()


def main() -> int:
    import uvicorn

    uvicorn.run("melody_architect.webapp:app", host="127.0.0.1", port=8765, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
