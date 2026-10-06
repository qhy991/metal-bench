# Compiler development and independent evaluation

## 1. Develop Cake in open-cake-ir

Use the [Metal development task preparation command](https://github.com/qhy991/open-cake-ir/blob/metal/docs/METAL_DEVELOPMENT_TASKS.md)
to materialize main's registered tasks in separate external folders. The task catalog
owns their semantics. Preserve unsupported dtypes and operations as explicit gaps.

Within a kernel search, freeze the Compiler commit. Explore structurally different
Cake candidates, run construction/verifier checks, inspect the author's own emitted
MSL, and evaluate survivors. MSL is inspectable generated source; it is not Apple GPU
machine code or a PTX equivalent. AIR/metallib artifacts and profiler observations
have different evidential scope; never infer instruction counts from MSL alone.
Reference visibility follows the authoring arm: a clean-start author cannot inspect
the native reference shipped by this public repository during a controlled study.

Every completed development task should retain a diagnosis with:

- The fixed task shape, dtype, Compiler commit, candidate and observed failure or limit.
- A minimal reproducer, relevant emitted source region and localized diagnostic.
- Correctness, raw timing and available profiler evidence; explicitly mark missing data.
- The responsible owner: candidate, verifier, cost model or IR vocabulary.
- A proposed change and a counterexample/regression that would test it.

Do not require the author to invent a Compiler defect. A good result can say the
current primitives suffice. Repeated independent findings justify a Compiler proposal;
one unusual latency or one candidate failure does not justify a new rule.

End the frozen search before changing Compiler source. Evaluate the proposal against
P1-P8, evolve primitives and analyses together, pass the Corpus Gate, and obtain the
required human release judgement. Then start a new development cycle at the successor
Compiler commit. Historical evaluations remain attached to their original commit.

## 2. Evaluate a frozen Cake in metal-bench

This repository owns an independent task specification, oracle, tolerances and timing
contract. It accepts ordinary MSL through the same candidate interface as native code;
its evaluator has no Cake imports. A single-shape adapter bundle covers only that
shape. It does not confer support for other cases in the suite.

First qualify the runner and candidate on the exact device, then evaluate the full
requested correctness set before recording timing. Preserve 30 raw samples with 64
dispatches each, their normalized arithmetic mean, failures and environment identity.
Native compilation and CPU harness checks are preliminary software evidence only.

Authoring may continue to use GLM-5.3 through the separately qualified provider. Keep
provider credentials and generated runs outside both repositories. For comparisons,
fix model/scaffold, reference access, task and stopping rules; record token usage
without imposing a token budget. This repository does not introduce another agent loop.

## 3. Interpret the result at its actual scope

The initial RMSNorm suite is public development material. Using it to improve Cake
is useful but cannot subsequently establish unseen-task generalization. A future
evaluation split must be versioned and its exposure recorded before authors use it.

Separate two questions: does a Compiler revision improve outcomes under a matched
authoring setup, and does Cake help an author relative to another authoring environment?
The second requires matched arms, qualified references and repeated runs. Neither is
answered by one fast kernel. Retain unsuccessful attempts, authoring time, tool calls,
token accounting and recurring diagnostics alongside accepted performance results.

Bench findings may feed the next development cycle. Keep the evaluator fixed for the
current evaluation; propose oracle, tolerance or task changes as separately reviewed
benchmark successors, never edits made to accommodate a candidate's failure.
