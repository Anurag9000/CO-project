# CO-project training-control applicability audit — 2026-10-01

## Repository role

CO-project is a pure Python assembler/simulator for a RISC-V-style instruction
subset. Its retained runtime consists of `Assembler.py` and `Simulator.py`,
using only Python standard-library operations and sequential branch-heavy state
updates. There is no retained ML model, optimizer, tensor framework, training
dataset, GPU kernel or numerical array backend.

GPU-first model training, CUDA/CuPy substitution, optimizer checkpointing,
training early stopping and CPU/GPU numerical parity are therefore **not
applicable**. Adding them would manufacture a training surface that the
repository does not contain.

## Corrections made

The previous no-training authority could pass an empty or incomplete checkout.
It now requires both canonical runtime sources to exist and records missing
runtime files as unresolved. An empty source set also fails closed.

The root v41 profile previously applied native/exact training-resume and generic
workload-registry closure to its non-training audit job. Those requirements are
now disabled only for this audit profile while retained-source training
reachability, semantic training-surface checks, registry accounting, controller
pinning and strict coverage remain enabled.

`Simulator.py` contains an ordinary branch target local that the universal
workload heuristic can classify as a generic workload-like surface. Because the
repository has no training workload registry, workload-surface accounting is not
used as a training completion criterion here.

## Executed evidence

Current focused CI:
- OPF v20 training-control audit run `36880314345`: **success**. It compiled
  the launcher/authority/tests, passed runtime-source/injected-training
  regressions, passed the exhaustive v41 training-control audit and uploaded
  the certificate.
- Estate local certificate run `36880314216`: **success**.

These results close the **ML/training applicability question only**. They do not
prove functional correctness of every assembler encoding, simulator instruction
semantic, malformed-input path or assignment-specific expected-output suite.
Those are ordinary software correctness requirements, not CUDA/training work.
