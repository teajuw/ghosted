import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()

DATA_PATH = Path(__file__).parent.parent.parent / "data" / "experiment_results.json"


@router.get("/experiment-results")
async def experiment_results():
    if not DATA_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Experiment results not yet generated. Run: python3 scripts/run_experiment.py",
        )
    return json.loads(DATA_PATH.read_text())
