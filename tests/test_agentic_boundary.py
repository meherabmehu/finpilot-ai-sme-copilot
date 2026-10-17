"""Development boundary tests that do not require redistribution of the proprietary benchmark."""
import ast
import os
from pathlib import Path
import subprocess
import sys

import pytest

from evaluation.agentic.selectors import resolve

ROOT = Path(__file__).resolve().parents[1]


def test_cli_requires_opt_in_before_database_setup(tmp_path):
    environment = os.environ.copy()
    environment.pop('FINPILOT_EVAL_DJANGO', None)
    result = subprocess.run([sys.executable, '-m', 'evaluation.agentic.run', '--benchmark-root', str(tmp_path),
                             '--out-dir', str(tmp_path / 'results')], env=environment, capture_output=True, text=True)
    assert result.returncode == 2
    assert 'no database was touched' in result.stderr
    assert not (tmp_path / 'results').exists()


def test_adapter_has_no_oracle_or_reference_imports():
    for path in (ROOT / 'evaluation/agentic').glob('*.py'):
        if path.name == 'run.py':
            continue  # trusted benchmark/scoring host, not the application-input adapter
        tree = ast.parse(path.read_text())
        modules = [node.module or '' for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        modules += [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        assert not any(name.startswith(('oracles', 'generators', 'adapters.reference', 'scoring')) for name in modules)
    text = (ROOT / 'evaluation/agentic/adapter.py').read_text()
    assert "'criteria'" not in text
    assert 'expected.' not in text


def test_selector_uses_actual_state_and_preserves_inputs():
    state = {'as_of': '2026-01-01', 'projection': {'available': True, 'funding_gap': '23.45'}, 'events': [
        {'id': 'tx:77', 'date': '2026-01-02', 'amount': '100.01', 'direction': 'outflow', 'payroll': True,
         'critical': False, 'category': 'Salaries & Wages'}]}
    plans = [{'name': 'Test', 'actions': [{'kind': 'split', 'event_id': '@payroll', 'amount': '@half', 'days': 2}]}]
    result = resolve(state, plans)
    assert result[0]['actions'][0]['event_id'] == 'tx:77'
    assert result[0]['actions'][0]['amount'] == '50.01'
    assert plans[0]['actions'][0]['event_id'] == '@payroll'
    assert state['events'][0]['amount'] == '100.01'
    with pytest.raises(ValueError, match='cannot resolve'):
        resolve(state, [{'name': 'Unknown', 'actions': [{'kind': 'shift', 'event_id': '@category:Missing', 'days': 1}]}])


def test_development_package_is_not_deployed():
    assert 'evaluation' in (ROOT / '.vercelignore').read_text().splitlines()
    assert 'evaluation' not in (ROOT / 'config/settings.py').read_text()


def test_postgres_requires_explicit_local_test_marker(tmp_path):
    from evaluation.agentic.database import isolated_database
    with pytest.raises(ValueError, match='marked'):
        with isolated_database(tmp_path):
            pytest.fail('unsafe database accepted')
