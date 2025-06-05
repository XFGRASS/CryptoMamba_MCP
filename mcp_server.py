import os
import sys
import uuid
import threading
from typing import List, Dict, Any

from pydantic import BaseModel
from mcp.server import FastMCP

# add project root to path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from scripts import training, evaluation, one_day_pred, simulate_trade

# initialize MCP server
app = FastMCP("CryptoMamba MCP Server")

# simple task registry
TASKS: Dict[str, Dict[str, Any]] = {}

class TrainRequest(BaseModel):
    config: str
    logger_type: str = "tb"
    accelerator: str = "gpu"
    devices: int = 1
    batch_size: int = 32
    num_workers: int = 4
    seed: int = 23
    save_checkpoints: bool = False
    use_volume: bool | None = None
    max_epochs: int | None = None

class EvalRequest(BaseModel):
    config: str
    ckpt_path: str
    batch_size: int = 32
    num_workers: int = 4
    use_volume: bool | None = None

class PredictRequest(BaseModel):
    config: str
    ckpt_path: str
    data_path: str = "data/one_day_pred.csv"
    date: str | None = None
    risk: int = 2
    use_volume: bool = False

class TradeRequest(BaseModel):
    config: str
    ckpt_path: str | None = None
    split: str = "test"
    trade_mode: str = "smart"
    batch_size: int = 32
    num_workers: int = 4
    balance: float = 100
    risk: float = 2


def run_training_async(task_id: str, req: TrainRequest):
    TASKS[task_id]["status"] = "running"
    try:
        args = [
            "--config", req.config,
            "--logger_type", req.logger_type,
            "--accelerator", req.accelerator,
            "--devices", str(req.devices),
            "--batch_size", str(req.batch_size),
            "--num_workers", str(req.num_workers),
            "--seed", str(req.seed),
        ]
        if req.save_checkpoints:
            args.append("--save_checkpoints")
        if req.use_volume:
            args.append("--use_volume")
        if req.max_epochs is not None:
            args.extend(["--max_epochs", str(req.max_epochs)])
        training.main(args)
        TASKS[task_id]["status"] = "completed"
    except Exception as e:
        TASKS[task_id]["status"] = f"failed: {e}"


def run_evaluation(req: EvalRequest) -> Dict[str, Any]:
    args = [
        "--config", req.config,
        "--ckpt_path", req.ckpt_path,
        "--batch_size", str(req.batch_size),
        "--num_workers", str(req.num_workers),
    ]
    if req.use_volume:
        args.append("--use_volume")
    return evaluation.main(args)


def run_prediction(req: PredictRequest) -> Dict[str, Any]:
    args = [
        "--config", req.config,
        "--ckpt_path", req.ckpt_path,
        "--data_path", req.data_path,
        "--risk", str(req.risk),
    ]
    if req.date:
        args.extend(["--date", req.date])
    if req.use_volume:
        args.append("--use_volume")
    return one_day_pred.main(args)


def run_trade(req: TradeRequest) -> Dict[str, Any]:
    args = [
        "--config", req.config,
        "--split", req.split,
        "--trade_mode", req.trade_mode,
        "--batch_size", str(req.batch_size),
        "--num_workers", str(req.num_workers),
        "--balance", str(req.balance),
        "--risk", str(req.risk),
    ]
    if req.ckpt_path:
        args.extend(["--ckpt_path", req.ckpt_path])
    return simulate_trade.main(args)


@app.tool(description="List available training configs")
def list_training_configs() -> List[str]:
    """Return available config names under configs/training."""
    path = os.path.join(ROOT, "configs", "training")
    return [x.replace(".yaml", "") for x in os.listdir(path) if x.endswith(".yaml")]


@app.tool(description="Start a training job")
def start_training(req: TrainRequest) -> Dict[str, str]:
    """Launch training in a background thread and return a task id."""
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {"status": "pending"}
    thread = threading.Thread(target=run_training_async, args=(task_id, req), daemon=True)
    TASKS[task_id]["thread"] = thread
    thread.start()
    return {"task_id": task_id}


@app.tool(description="Get status of a training task")
def task_status(task_id: str) -> Dict[str, Any]:
    """Return the status dictionary for a given task id."""
    return TASKS.get(task_id, {"status": "unknown"})


@app.tool(description="Evaluate a model checkpoint")
def evaluate_model(req: EvalRequest) -> Dict[str, Any]:
    """Run evaluation for the provided checkpoint."""
    return run_evaluation(req)


@app.tool(description="Predict the next day price")
def predict_next_day(req: PredictRequest) -> Dict[str, Any]:
    """Run one-day prediction using a trained model."""
    return run_prediction(req)


@app.tool(description="Run a trading simulation")
def simulate(req: TradeRequest) -> Dict[str, Any]:
    """Simulate trading based on model predictions."""
    return run_trade(req)


if __name__ == "__main__":
    app.run(transport="streamable-http")

