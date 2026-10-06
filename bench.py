#!/usr/bin/env python3
"""Independent correctness first, then optional Metal GPU microbenchmark."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from metalbench.rmsnorm import inputs, reference, compare, mean30

ROOT = Path(__file__).resolve().parent


def candidate_variant(path, case):
    doc = json.loads(path.read_text())
    if doc.get('schema_version') != 1 or doc.get('kind') != 'msl' or doc.get('task') != 'rmsnorm_fp32':
        raise ValueError('candidate manifest schema/task differs')
    variant = doc['variants'].get(case)
    if variant is None:
        raise ValueError(f'candidate does not implement {case}; no fallback')
    source = (path.parent / variant['source']).resolve(strict=True)
    if not source.is_relative_to(path.parent.resolve()):
        raise ValueError('candidate source must be in its bundle')
    if type(variant.get('threads')) is not int or not 1 <= variant['threads'] <= 1024:
        raise ValueError('invalid threadgroup size')
    if type(variant.get('parameters')) is not bool or not isinstance(variant.get('entry'), str):
        raise ValueError('invalid entry/parameters')
    return {**variant, 'source': str(source)}


def evaluate(args):
    definition = json.loads((ROOT/'tasks/rmsnorm_fp32/task.json').read_text())
    suite = json.loads((ROOT/'suite.json').read_text())
    selected = [w for w in definition['workloads'] if args.workload in ('all', w['id'])]
    if not selected:
        raise ValueError('unknown workload')
    if args.command == 'bench' and args.backend != 'metal':
        raise ValueError('CPU checks never produce GPU timing')
    if args.backend == 'metal' and args.runner is None:
        raise ValueError('provide an explicitly built native runner')
    output = args.output.resolve()
    if any((p/'.git').exists() for p in (output,*output.parents)):
        raise ValueError('results must be outside source checkouts')
    output.mkdir(parents=True, exist_ok=False)
    report = {'suite': suite['suite_id'], 'task': definition['id'], 'backend': args.backend,
              'scope': 'development', 'candidate': str(args.candidate.resolve()),
              'checks': [], 'timings': [], 'status': 'started', 'full_device_correctness': False,
              'token_policy': 'accounting_only', 'other_gpu_clients': 'not_excluded'}
    variants = {}

    def invoke(w, distribution, seed, timing=False):
        x, weight = inputs(w['rows'], w['columns'], distribution, seed)
        job = {**w, 'x': x, 'weight': weight, 'epsilon': definition['epsilon'], 'timing': timing}
        expected = reference(x,weight,w['rows'],w['columns'],definition['epsilon'])
        if args.backend == 'metal':
            job.update(variants[w['id']])
            job['expected_device'] = suite['target']['device_name']
        with tempfile.TemporaryDirectory(prefix='metal-bench-job-') as temp:
            job_path = Path(temp)/'job.json'; job_path.write_text(json.dumps(job))
            command = ([str(args.runner.resolve()), str(job_path)] if args.backend == 'metal' else
                       [sys.executable, str(ROOT/'metalbench/python_worker.py'), str(args.candidate.resolve()), str(job_path)])
            result = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
        if result.returncode:
            raise ValueError('candidate execution failed: '+result.stderr[-2000:])
        value = json.loads(result.stdout)
        if value.get('inputs_unchanged') is not True:
            raise ValueError('missing input-integrity result')
        if args.backend == 'metal' and value.get('device') != suite['target']['device_name']:
            raise ValueError('device mismatch')
        error = compare(expected,value['output'],atol=definition['atol'],rtol=definition['rtol'])
        row = {'workload':w['id'],'distribution':distribution,'seed':seed,'max_abs_error':error}
        if timing:
            raw = value.get('gpu_buffer_ms')
            row.update(raw_gpu_buffer_ms=raw,mean_dispatch_ms=mean30(raw),samples=30,
                       dispatches_per_sample=64,interval=suite['timing']['scope'],reset=suite['timing']['reset'])
        return row

    try:
        if args.backend == 'metal':
            variants = {w['id']:candidate_variant(args.candidate,w['id']) for w in selected}
        for w in selected:
            for mode in definition['distributions']:
                for seed in definition['seeds']:
                    report['checks'].append(invoke(w,mode,seed))
        report['full_device_correctness'] = args.backend == 'metal' and args.workload == 'all'
        if args.command == 'bench':
            # Fresh input after the entire requested correctness gate passes.
            for w in selected:
                report['timings'].append(invoke(w,'uniform',997,timing=True))
        report['status']='passed'
    except (ValueError, OSError, KeyError, TypeError, OverflowError, subprocess.TimeoutExpired) as error:
        report.update(status='failed',error=str(error))
    (output/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('list','check','bench'))
    p.add_argument('--backend',choices=('cpu','metal'),default='cpu')
    p.add_argument('--candidate',type=Path)
    p.add_argument('--runner',type=Path)
    p.add_argument('--workload',default='all')
    p.add_argument('--output',type=Path)
    p.add_argument('--timeout',type=float,default=60)
    a=p.parse_args()
    if a.command=='list':
        print((ROOT/'tasks/rmsnorm_fp32/task.json').read_text()); return 0
    if a.candidate is None or a.output is None: p.error('candidate and output are required')
    if not math.isfinite(a.timeout) or a.timeout<=0: p.error('timeout must be finite and positive')
    report=evaluate(a)
    print(json.dumps({'status':report['status'],'checks':len(report['checks']),'timings':len(report['timings']),'report':str(a.output/'report.json')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
