# metal-bench

Independent Apple Metal task evaluation, separate from Cake Compiler development.
The initial **public development suite** contains FP32 RMSNorm at three shapes,
five input distributions and two seeds: 30 correctness cases. It is not a held-out
benchmark or a claim of Cake advantage. No upstream task datasets are redistributed.

The mathematical oracle and candidate comparator have **no Cake dependency**. Cake
exports ordinary MSL through a small packaging adapter; native candidates use the
same manifest, oracle and Metal runner. The CPU path checks the harness, not GPU support.

## CPU checks

Python 3.10+ standard library only. Write reports to new directories outside Git.

```sh
python3 bench.py list
python3 bench.py check --backend cpu --candidate examples/rmsnorm_cpu.py \
  --output /tmp/metal-bench-cpu-check
python3 -m unittest discover -s tests -v
```

The CPU candidate ABI is `run(x, weight, rows, columns, epsilon) -> flat_output`.
Inputs and outputs have FP32 semantics; the external oracle accumulates with Python
float64 and checks the task's declared tolerance. Input mutation, nonfinite values,
wrong shapes and candidate process failures are refused. Subprocesses have a timeout,
but candidates are trusted code: this is not hostile-code or author-read isolation.

## Metal route

The initial native ABI binds x/weight/output at buffers 0/1/2, one threadgroup per
row; a manifest declares entry, threads and whether columns/epsilon use buffers 3/4.
Every workload needs an explicit variant; missing variants never fall back to Python.
The supplied native kernel is an integration baseline, **not a qualified strong baseline**.

```sh
DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer \
SDKROOT=/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX15.0.sdk \
  sh scripts/build_runner.sh /tmp/metal-bench-native-build

python3 bench.py check --backend metal --candidate examples/rmsnorm_metal.json \
  --runner /tmp/metal-bench-native-build/metal-bench-runner --output /tmp/metal-bench-device-check
python3 bench.py bench --backend metal --candidate examples/rmsnorm_metal.json \
  --runner /tmp/metal-bench-native-build/metal-bench-runner --output /tmp/metal-bench-device-timing
```

These are explicit device commands, not evidence they have passed. Current verification
and missing qualification are listed in [VALIDATION.md](docs/VALIDATION.md).
The exact initial target is Apple M4 / apple9. No M1/M2 substitution. The runner
uses the existing `open-cake-ir-metal-<uid>.lock` allocation filename for cooperation
with local Cake jobs, without importing Cake. This is a shared lock convention, not
a dependency on its runtime or a claim of machine-wide exclusivity.

`bench` first completes all requested correctness cases, then measures fresh inputs.
Each workload records all 30 GPU command-buffer intervals, 64 dispatches per buffer,
and the arithmetic mean divided by 64. Three batched warmups are excluded. Inputs
remain resident; caches are not flushed; other GPU activity is not excluded. All
buffer outputs are checked against the single-dispatch output, which is checked by
the external oracle. These are amortized GPU intervals, not framework end-to-end time.
No relative performance claim is produced automatically from separately run candidates.

## Cake handoff

Export the matching exact-shape RMSNorm MSL from a fixed Cake version, then:

```sh
python3 scripts/package_cake_msl.py --source /path/to/starter.metal \
  --entry cake_rmsnorm_fp32 --case r128-c1024 --output /tmp/cake-rmsnorm-bundle
python3 bench.py check --backend metal --candidate /tmp/cake-rmsnorm-bundle/candidate.json \
  --workload r128-c1024 --runner /path/to/metal-bench-runner --output /tmp/cake-rmsnorm-check
```

This one-case handoff cannot claim full-suite device correctness. Compilation,
correctness, hardware timing and framework end-to-end acceptance remain separate.
Compiler development tasks stay in open-cake-ir; this repository fixes its own task
definitions independently of what a Compiler currently supports. Token use is only
an observed cost, never a stopping or score eligibility condition.

Future work: qualified strong references, end-to-end framework timing, additional
task families and versioned evaluation splits. Preserve unsupported cases instead of
quietly changing the suite to match Cake's current capabilities.
