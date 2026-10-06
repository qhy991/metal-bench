import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import bench
from metalbench.rmsnorm import inputs, reference, compare, mean30

ROOT=Path(__file__).resolve().parents[1]


class OracleTests(unittest.TestCase):
    def test_small_analytic_result(self):
        out=reference([3,4],[2,1],1,2,0.0)
        self.assertAlmostEqual(out[0],6/math.sqrt(12.5),places=6)
        self.assertAlmostEqual(out[1],4/math.sqrt(12.5),places=6)

    def test_seed_reproducibility_and_new_inputs(self):
        a=inputs(3,257,'uniform',101)
        self.assertEqual(a,inputs(3,257,'uniform',101))
        self.assertNotEqual(a,inputs(3,257,'uniform',307))

    def test_zero_inputs_remain_zero(self):
        x,w=inputs(3,257,'zeros',101)
        self.assertEqual(reference(x,w,3,257,1e-5),[0.0]*771)

    def test_invalid_outputs_refused(self):
        for value in ([0.0], [float('nan'),1.0], [float('inf'),1.0], [True,1.0], [1.1,1.0]):
            with self.subTest(value=value),self.assertRaises(ValueError):
                compare([1.0,1.0],value,atol=1e-5,rtol=1e-5)

    def test_mean_keeps_outlier_and_normalizes_64(self):
        samples=[64.0]*29+[640.0]
        self.assertEqual(mean30(samples),1.3)
        self.assertEqual(len(samples),30)

    def test_invalid_timing_refused(self):
        for samples in ([1.0]*29,[1.0]*31,[1.0]*29+[0.0],[1.0]*29+[float('nan')]):
            with self.subTest(samples=samples),self.assertRaises(ValueError): mean30(samples)


class HarnessTests(unittest.TestCase):
    def args(self,output,**kwargs):
        return SimpleNamespace(command='check',backend='cpu',candidate=ROOT/'examples/rmsnorm_cpu.py',
            runner=None,workload='all',output=output,timeout=10,**kwargs)

    def test_all_cpu_cases_cannot_be_device_qualification(self):
        with tempfile.TemporaryDirectory() as temp:
            r=bench.evaluate(self.args(Path(temp)/'result'))
            self.assertEqual(r['status'],'passed')
            self.assertEqual(len(r['checks']),30)
            self.assertFalse(r['full_device_correctness'])
            self.assertEqual(r['timings'],[])

    def test_bad_candidate_stops_and_retains_report(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp); code=p/'bad.py';code.write_text('def run(x,w,r,c,e): return [0.0]*(r*c)\n')
            args=self.args(p/'result');args.candidate=code
            r=bench.evaluate(args)
            self.assertEqual(r['status'],'failed')
            self.assertEqual(r['checks'],[])
            self.assertTrue((p/'result/report.json').exists())

    def test_mutation_refused_even_with_correct_output(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);code=p/'mutating.py'
            code.write_text((ROOT/'examples/rmsnorm_cpu.py').read_text().replace('    return result','    x[0] = 10000\n    return result'))
            a=self.args(p/'result');a.candidate=code
            r=bench.evaluate(a)
            self.assertEqual(r['status'],'failed')
            self.assertIn('mutated inputs',r['error'])

    def test_existing_result_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(FileExistsError): bench.evaluate(self.args(Path(temp)))

    def test_cpu_timing_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            a=self.args(Path(temp)/'result');a.command='bench'
            with self.assertRaisesRegex(ValueError,'never produce'):bench.evaluate(a)

    def test_missing_variant_and_path_escape_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp);manifest=p/'candidate.json'
            base={'schema_version':1,'kind':'msl','task':'rmsnorm_fp32','variants':{}}
            manifest.write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError,'no fallback'):bench.candidate_variant(manifest,'r1-c32')
            base['variants']['r1-c32']={'source':str(ROOT/'examples/rmsnorm.metal'),'entry':'rmsnorm','threads':32,'parameters':True}
            manifest.write_text(json.dumps(base))
            with self.assertRaisesRegex(ValueError,'in its bundle'):bench.candidate_variant(manifest,'r1-c32')

    def test_wrong_correctness_never_reaches_timing(self):
        with tempfile.TemporaryDirectory() as temp:
            a=self.args(Path(temp)/'result');a.backend='metal';a.command='bench'
            a.candidate=ROOT/'examples/rmsnorm_metal.json';a.runner=Path('/mock/not-executed')
            calls=[]
            def fake(command,**kwargs):
                job=json.loads(Path(command[-1]).read_text());calls.append(job['timing'])
                return subprocess.CompletedProcess(command,0,json.dumps({'output':[0.0]*len(job['x']),'device':'Apple M4','inputs_unchanged':True}),'')
            with patch.object(bench.subprocess,'run',side_effect=fake):r=bench.evaluate(a)
            self.assertEqual(r['status'],'failed');self.assertEqual(calls,[False])

    def test_candidate_failure_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            a=self.args(Path(temp)/'result')
            with patch.object(bench.subprocess,'run',side_effect=subprocess.TimeoutExpired('candidate',1)):
                r=bench.evaluate(a)
            self.assertEqual(r['status'],'failed')

    def test_evaluator_has_no_cake_dependency(self):
        import ast
        for path in [ROOT/'bench.py',*(ROOT/'metalbench').glob('*.py')]:
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node,ast.Import): names=[a.name for a in node.names]
                elif isinstance(node,ast.ImportFrom):names=[node.module or '']
                else:continue
                self.assertFalse(any(n.startswith('open_cake_ir') for n in names),path)


if __name__=='__main__':unittest.main()
