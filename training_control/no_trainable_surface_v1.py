#!/usr/bin/env python3
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".training_control", "training_control", "__pycache__", ".venv", "venv", "build", "dist"}
TRAINING_ATTRS = {"fit", "fit_generator", "partial_fit", "train_on_batch", "backward", "zero_grad", "step", "training_step", "optimizer_step", "manual_backward"}
TRAINING_NAMES = {"Trainer", "Seq2SeqTrainer", "TrainingArguments", "Optimizer", "SGD", "Adam", "AdamW", "Adagrad", "Adadelta", "RMSprop", "LBFGS", "SparseAdam"}
TRAINING_MODULE_PREFIXES = ("torch.optim", "tensorflow.keras.optimizers", "keras.optimizers", "pytorch_lightning", "lightning.pytorch")

@dataclass(frozen=True, slots=True)
class Finding:
    path: str
    line: int
    kind: str
    symbol: str

class Scanner(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.findings: list[Finding] = []
    def add(self, node: ast.AST, kind: str, symbol: str) -> None:
        self.findings.append(Finding(self.path.relative_to(ROOT).as_posix(), int(getattr(node, "lineno", 0) or 0), kind, symbol))
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name.startswith(TRAINING_MODULE_PREFIXES): self.add(node, "training_import", alias.name)
        self.generic_visit(node)
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if module.startswith(TRAINING_MODULE_PREFIXES): self.add(node, "training_import", module)
        for alias in node.names:
            if alias.name in TRAINING_NAMES: self.add(node, "training_symbol_import", f"{module}.{alias.name}".strip("."))
        self.generic_visit(node)
    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in TRAINING_ATTRS: self.add(node, "training_call", func.attr)
        elif isinstance(func, ast.Name) and func.id in TRAINING_NAMES: self.add(node, "training_constructor", func.id)
        self.generic_visit(node)

def audit() -> dict[str, object]:
    findings: list[Finding] = []
    parse_errors: list[dict[str, object]] = []
    files = [p for p in ROOT.rglob("*.py") if p.name != "run_all_training.py" and not any(part in EXCLUDED_PARTS for part in p.relative_to(ROOT).parts)]
    for path in sorted(files):
        try: tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except SyntaxError as exc:
            parse_errors.append({"path": path.relative_to(ROOT).as_posix(), "line": int(exc.lineno or 0), "message": str(exc)})
            continue
        scanner = Scanner(path); scanner.visit(tree); findings.extend(scanner.findings)
    unresolved: list[dict[str, object]] = []
    if parse_errors: unresolved.append({"type": "python_parse_errors", "values": parse_errors})
    if findings: unresolved.append({"type": "retained_training_primitives_detected", "values": [asdict(x) for x in findings]})
    return {"schema_version": 1, "repository": "Anurag9000/CO-project", "classification": "non_trainable_assembler_simulator" if not unresolved else "training_surface_detected", "retained_python_files": [p.relative_to(ROOT).as_posix() for p in sorted(files)], "training_findings": [asdict(x) for x in findings], "parse_errors": parse_errors, "unresolved": unresolved, "complete": not unresolved, "source_configuration_only": True, "training_executed_by_audit": False}
