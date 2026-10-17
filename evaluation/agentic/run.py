"""Run the unchanged external benchmark against actual, isolated Django services.

FINPILOT_EVAL_DJANGO=1 python -m evaluation.agentic.run --benchmark-root PATH --suite full --out-dir PATH
No source archive, oracle or third-party prior is vendored into the public application.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark-root', type=Path, required=True)
    parser.add_argument('--suite', default='full', choices=['core', 'policy', 'counterfactual', 'financing', 'data_quality', 'adversarial', 'decision_memory', 'full'])
    parser.add_argument('--adapter', choices=['django'], default='django')
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--case', action='append')
    parser.add_argument('--postgres-socket', type=Path, help='Explicit disposable local test cluster, never a production URL')
    parser.add_argument('--postgres-port', type=int, default=55433)
    args = parser.parse_args(argv)
    if os.environ.get('FINPILOT_EVAL_DJANGO') != '1':
        parser.error('Explicit FINPILOT_EVAL_DJANGO=1 required; no database was touched')
    if 'django.conf' in sys.modules:
        parser.error('Run in a fresh Python process; settings may already be configured')
    source = args.benchmark_root.resolve()
    required = ['scripts/run_evaluation.py', 'schemas/evaluation_result.schema.json', 'scenarios/index.json', 'LICENSE-NOTICE.md']
    if not all((source / p).is_file() for p in required):
        parser.error('Incomplete external benchmark root')
    # Do not permit output under static or the source package itself.
    output = args.out_dir.resolve()
    if output.is_relative_to(source) or any(output.is_relative_to(ROOT / p) for p in ('static', 'staticfiles', 'media')):
        parser.error('Use a non-public, separate output directory')
    from .database import isolated_database
    with isolated_database(args.postgres_socket, args.postgres_port) as database_label:
        return execute(args, source, output, database_label)


def execute(args, source, output, database_label):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'evaluation.agentic.settings'
    os.environ['DEBUG'] = 'true'
    os.environ.pop('VERCEL', None)
    os.environ.pop('RENDER', None)
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection
    if connection.settings_dict['NAME'] != ':memory:' and not (
            connection.vendor == 'postgresql' and connection.settings_dict['NAME'] == os.environ.get('FINPILOT_EVAL_DB_NAME')):
        raise RuntimeError('Refusing a non-isolated database')
    call_command('migrate', verbosity=0, interactive=False)
    sys.path.insert(0, str(source))
    spec = importlib.util.spec_from_file_location('external_agentic_runner', source / 'scripts/run_evaluation.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    from .adapter import DjangoAdapter
    adapter = DjangoAdapter(output / 'actual')
    runner.get_adapter = lambda name: adapter
    report = runner.run(args.suite, 'django', only=args.case, out_dir=output, write_reports=False)
    # info() is called before cases by the upstream runner; set only after actual execution.
    report['adapter']['tested_against_live_application'] = adapter.executed > 0
    import jsonschema
    jsonschema.validate(report, json.loads((source / 'schemas/evaluation_result.schema.json').read_text()))
    output.mkdir(parents=True, exist_ok=True)
    stem = f"evaluation_{args.suite}_django"
    (output / f'{stem}.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    (output / f'{stem}.md').write_text(runner.render_markdown(report))
    manifest = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(source.rglob('*')) if p.is_file() and p.suffix in ('.py', '.json', '.yaml', '.md')
                and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and 'runs' not in p.parts}
    metadata = {'adapter_file_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                        for p in sorted((ROOT / 'evaluation/agentic').glob('*.py'))},
                'application_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'working_tree': subprocess.check_output(['git', 'diff', '--stat'], cwd=ROOT, text=True),
                'python': platform.python_version(), 'django': django.get_version(),
                'database': database_label + '; per-case rollback', 'llm': 'not used',
                'benchmark_file_sha256': manifest, 'cases_attempted': report['selected_cases'],
                'cases_completed_actual_services': adapter.executed, 'schema_validation': 'passed',
                'businesses_after_run': __import__('apps.portal.models', fromlist=['Business']).Business.objects.count()}
    (output / f'{stem}.environment.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'suite': args.suite, 'selected': report['selected_cases'], 'summary': report['summary']}, indent=2))
    if report['summary']['blocked']:
        return 3
    return 2 if report['summary']['failed'] or report['summary']['critical_failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
