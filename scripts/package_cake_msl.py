#!/usr/bin/env python3
"""Package an already emitted Cake source without importing Cake or reinterpreting IR.

This adapter supports the documented one-SIMD-group-per-row RMSNorm ABI only.
It does not grant correctness or infer shape compatibility from source spelling.
"""
import argparse
import json
from pathlib import Path
import shutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source',type=Path,required=True)
p.add_argument('--entry',required=True)
p.add_argument('--case',choices=('r1-c32','r3-c257','r128-c1024'),required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
source=a.source.resolve(strict=True)
a.output.mkdir(parents=True,exist_ok=False)
shutil.copyfile(source,a.output/'candidate.metal')
(a.output/'candidate.json').write_text(json.dumps({'schema_version':1,'kind':'msl','task':'rmsnorm_fp32',
 'variants':{a.case:{'source':'candidate.metal','entry':a.entry,'threads':32,'parameters':False}}},indent=2)+'\n')
print(a.output/'candidate.json')
