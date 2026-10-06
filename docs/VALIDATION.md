# Validation scope

Initial source includes independent oracle/comparator, CPU candidate subprocess,
Metal manifest/runner, raw 30x64 mean reporting and a Cake MSL handoff adapter.

CPU tests and native source compilation do not establish device correctness or
performance. No GPU qualification, strong-baseline or held-out superiority claim is
made by this initial repository. Actual checks will be appended with commit and scope.

The first task is original integration/development material. It is not the full
SOL-ExecBench RMSNorm problem and must not be labeled as an upstream task migration.
No third-party task data, model credentials or private experiment logs are included.

## 2026-10-06 initial software validation

Executable source: commit `2045bc6`, tested from a separate committed checkout.

- Python contract tests: **15 passed**. They exercise incorrect output, input
  mutation, timeout, missing variants, invalid timing samples, and refusal to time
  a candidate before its correctness checks pass.
- CPU candidate CLI: **30 correctness cases passed**, zero GPU timings.
- Cake handoff: the emitted `cake_rmsnorm_fp32` MSL for `r128-c1024` was packaged
  and its manifest resolved successfully. This checks the artifact interface only.
- Swift runner: compiled successfully with Xcode 16's Swift compiler and
  MacOSX15.0 SDK, targeting arm64 macOS 15, using a separate temporary module cache.
  The compiler emitted a deprecation warning for `fastMathEnabled`; no GPU was run.

No native candidate or Cake candidate has passed device qualification in this
repository yet. No measured speedup, profiler result, framework end-to-end result
or held-out evaluation follows from these software checks.
