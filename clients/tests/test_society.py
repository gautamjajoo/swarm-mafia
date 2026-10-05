"""Contract tests for reproducible, separately stored producer-declared traces."""
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from observatory_client.api import ClientError, MAX_TRACE_BYTES, ObservatoryAPI
from observatory_client.cli import main

RUN_ID = 'society-' + 'a' * 24


@pytest.fixture
def payload():
    return json.loads((Path(__file__).resolve().parents[2] / 'examples' / 'society-events.json').read_text())


def test_saved_version_route_mapping_preserves_producer_status(api_server, payload):
    expected = {'source_ref': {'id': RUN_ID, 'version': 2, 'hash': 'fixture-hash'},
                'evidence_status': 'producer_declared', 'limitations': ['not causal'], 'truncated': True}
    api_server['payload'] = expected
    api = ObservatoryAPI(api_server['url'], 'fixture-token')
    assert api.trace_protocol() == expected
    assert api.trace_import(payload) == expected
    api.trace_runs(limit=7)
    api.trace_run(RUN_ID)
    api.trace_run(RUN_ID, version=2)
    assert api.trace_graph(RUN_ID, version=2, seed='tool:path/id', hops=2) == expected
    assert api.trace_review(RUN_ID, version=2) == expected
    assert api.trace_review(RUN_ID, version=2, question='What happened next?') == expected
    requests = api_server['requests']
    assert [urlsplit(r['path']).path for r in requests] == [
        '/v1/society/protocol', '/v1/society/runs', '/v1/society/runs',
        '/v1/society/runs/' + RUN_ID, '/v1/society/runs/' + RUN_ID,
        '/v1/society/runs/' + RUN_ID + '/graph',
        '/v1/society/runs/' + RUN_ID + '/review',
        '/v1/society/runs/' + RUN_ID + '/investigate']
    assert requests[1]['method'] == 'POST' and requests[1]['body'] == payload
    assert parse_qs(urlsplit(requests[2]['path']).query) == {'limit': ['7']}
    assert not urlsplit(requests[3]['path']).query
    assert parse_qs(urlsplit(requests[5]['path']).query) == {'version': ['2'], 'seed': ['tool:path/id'], 'hops': ['2']}
    assert requests[6]['method'] == 'GET'
    assert requests[7]['body'] == {'version': 2, 'question': 'What happened next?'}
    assert all(r['authorization'] == 'Bearer fixture-token' for r in requests)


@pytest.mark.parametrize('method,params', [
    ('trace_runs', {'limit': 101}), ('trace_runs', {'limit': True}),
    ('trace_run', {'run_id': '../secret'}), ('trace_run', {'run_id': RUN_ID, 'version': 0}),
    ('trace_run', {'run_id': RUN_ID, 'version': 1_000_000_001}),
    ('trace_graph', {'run_id': RUN_ID, 'version': None, 'seed': 'e1'}),
    ('trace_graph', {'run_id': RUN_ID, 'version': True, 'seed': 'e1'}),
    ('trace_graph', {'run_id': RUN_ID, 'version': 1, 'seed': 'event\n'}),
    ('trace_graph', {'run_id': RUN_ID, 'version': 1, 'seed': 'e1', 'hops': 3}),
    ('trace_review', {'run_id': RUN_ID, 'version': None}),
    ('trace_review', {'run_id': RUN_ID, 'version': 1, 'question': ''}),
    ('trace_review', {'run_id': RUN_ID, 'version': 1, 'question': 'x' * 4001}),
    ('trace_import', {'payload': {}}),
])
def test_invalid_scope_never_reaches_server(api_server, method, params):
    with pytest.raises(ClientError) as error:
        getattr(ObservatoryAPI(api_server['url'], 'fixture-token'), method)(**params)
    assert error.value.code == 'invalid_params'
    assert not api_server['requests']


@pytest.mark.parametrize('bad', ['oversized', 'deep', 'nonfinite', 'empty', 'many'])
def test_import_payload_budgets(api_server, payload, bad):
    if bad == 'oversized':
        payload['events'][0]['data']['name'] = 'x' * MAX_TRACE_BYTES
    elif bad == 'deep':
        value = {}
        for _ in range(14):
            value = {'next': value}
        payload['extra'] = value
    elif bad == 'nonfinite':
        payload['extra'] = float('nan')
    elif bad == 'empty':
        payload['events'] = []
    elif bad == 'many':
        payload['events'] = [{}] * 2001
    with pytest.raises(ClientError):
        ObservatoryAPI(api_server['url'], 'fixture-token').trace_import(payload)
    assert not api_server['requests']


def test_cli_import_and_reproducible_review(api_server, payload, monkeypatch, tmp_path, capsys):
    monkeypatch.setenv('OBSERVATORY_API_TOKEN', 'fixture-token')
    monkeypatch.setenv('OBSERVATORY_API_URL', api_server['url'])
    file = tmp_path / 'trace.json'
    file.write_text(json.dumps(payload))
    assert main(['trace-import', str(file)]) == 0
    assert api_server['requests'][-1]['body'] == payload
    assert main(['trace-review', RUN_ID, '--version', '2', '--question', 'Check recovery']) == 0
    assert api_server['requests'][-1]['body'] == {'version': 2, 'question': 'Check recovery'}
    capsys.readouterr()
    file.write_text('{"schema_version":"societylab.events.v1","schema_version":"other"}')
    assert main(['trace-import', str(file)]) == 1
    output = capsys.readouterr()
    assert not output.out
    assert json.loads(output.err)['error']['code'] == 'invalid_params'
    assert len(api_server['requests']) == 2


def test_import_connection_uncertainty_never_retries(api_server, payload):
    class Offline:
        calls = 0
        def open(self, *args, **kwargs):
            self.calls += 1
            raise TimeoutError
    opener = Offline()
    api = ObservatoryAPI(api_server['url'], 'fixture-token', opener=opener)
    with pytest.raises(ClientError, match='may have been saved'):
        api.trace_import(payload)
    assert opener.calls == 1


def test_import_conflict_is_not_raw_index_not_ready(api_server, payload):
    api_server.update(status=409, payload={"detail": "fixture-token private source text"})
    with pytest.raises(ClientError) as error:
        ObservatoryAPI(api_server["url"], "fixture-token").trace_import(payload)
    assert error.value.code == "conflict"
    assert error.value.status == 409
    assert "fixture-token" not in str(error.value)
    assert len(api_server["requests"]) == 1
