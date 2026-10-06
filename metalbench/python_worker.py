"""Trusted CPU candidate subprocess. This is timeout containment, not a sandbox."""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    candidate, job_path = sys.argv[1:]
    job = json.loads(Path(job_path).read_text())
    spec = importlib.util.spec_from_file_location('bench_candidate', candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    x, weight = list(job['x']), list(job['weight'])
    out = module.run(x, weight, job['rows'], job['columns'], job['epsilon'])
    if x != job['x'] or weight != job['weight']:
        raise ValueError('candidate mutated inputs')
    print(json.dumps({'output': out, 'inputs_unchanged': True, 'device': 'cpu'}, allow_nan=False))


if __name__ == '__main__':
    main()
