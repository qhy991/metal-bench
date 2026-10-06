# metal-bench

The benchmark owns task semantics, oracle, tolerances and measurement. Candidates
may use Cake or native Metal, but the evaluator must not import open_cake_ir, its
Verifier, its task oracle, Lab or provider modules. The suite remains usable without Cake.

Keep each task's specification in its own directory. Never silently replace dtype,
shape, target or unsupported cases. This v0.1 is a public DEVELOPMENT suite, not held-out.
If a task is used to improve a compiler, do not later claim it was unseen by that compiler.

Token use is recorded only; never introduce token budgets or token-based acceptance.
Use explicit time, turn and device-evaluation bounds in authoring jobs. The benchmark
does not implement another Ralph loop or store credentials. Authors write only their
candidate artifacts; maintenance proposals are reviewed outside a frozen evaluation.

Retain raw timings and failures. Thirty samples, 64 dispatches/sample, arithmetic mean
after normalization; no outlier trimming, retries or CV/IQR gate. Never equate these
GPU command-buffer intervals with framework end-to-end latency. Compare candidates
under matching scope; strong reference claims need full correctness and device evidence.

Native M4 work cooperates with the pre-existing per-user Metal allocation lock. CPU
orchestration is outside that lock. Other users and GUI activity are not excluded.
No device qualification follows from CPU tests or source compilation. Preserve exact
hardware/toolchain identity in qualification records. Do not rerun a failed environment
check after changing its environment and call it the same acceptance.

Run source tests at a committed checkout. Generated results/builds live outside Git.
Candidate subprocesses are trusted code, not an OS sandbox. Separate directory/HOME
does not provide read isolation; controlled studies must qualify their authoring boundary.
