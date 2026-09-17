"""The Dr. Health PWA picks install instructions from the user agent.

The logic lives in inline template JavaScript, which no linter or Python test
can see, so this drives it through node the same way AGENTS.md syntax-checks
inline scripts. Skips when node is unavailable rather than failing.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CASES = Path(__file__).resolve().parent / 'install_guide_cases.js'


@pytest.mark.skipif(shutil.which('node') is None, reason='node not installed')
def test_install_guide_matches_browser():
    result = subprocess.run(
        ['node', str(CASES)],
        cwd=str(REPO), capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        'install-instruction detection regressed:\n' + result.stdout + result.stderr
    )
    # Guard against the harness silently finding nothing to run.
    assert 'PASS' in result.stdout, result.stdout + result.stderr


def test_manifest_self_references_for_install_detection():
    """A browser tab can only tell the app is already installed via a
    self-referencing related_applications entry, which is what lets the
    install button hide itself."""
    import json
    manifest = json.loads(
        (REPO / 'static' / 'dr_health_manifest.json').read_text(encoding='utf-8')
    )
    related = manifest.get('related_applications') or []
    assert any(entry.get('platform') == 'webapp' for entry in related), related
    # Present-and-true would disqualify the app from being installable at all.
    assert manifest.get('prefer_related_applications') in (None, False)
