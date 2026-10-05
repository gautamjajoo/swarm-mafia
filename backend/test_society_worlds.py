import hashlib
import json
from pathlib import Path
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from society_worlds import PROVENANCE, ReplayRequest, replay, router
from vendor.society_lab.reference_repair_environment import ReferenceRepairEnvironment, create_reference_repair_spec


class WorldTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)
        self.actions = []
        self.seed = 42

    def state(self):
        response = self.client.post('/society/worlds/replay', json={'seed': self.seed, 'max_rounds': 10, 'actions': self.actions})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def step(self, action):
        state = self.state()
        self.actions.append({'role': state['next_role'], 'action': action})
        return self.state()

    def until_role(self, role):
        while self.state()['next_role'] != role:
            self.step({'action': 'wait'})

    def canonical(self):
        env = ReferenceRepairEnvironment(create_reference_repair_spec(max_rounds=10), self.seed)
        return env.observe('ethics_owner')['target_document']['your_copied_reference']

    def test_catalog_and_hashes_match_exact_upstream_files(self):
        data = self.client.get('/society/worlds/catalog').json()
        self.assertEqual(data['evidence_status'], 'human_steered_proxy')
        self.assertEqual(data['worlds'][0]['bounds']['max_actions'], 20)
        for source in PROVENANCE['files']:
            path = Path(__file__).parent / 'vendor' / 'society_lab' / Path(source['path']).name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source['sha256'])

    def test_same_seed_rebuilds_identical_state_and_events(self):
        self.step({'action': 'drive_search', 'query': 'IRB'})
        self.step({'action': 'wait'})
        self.assertEqual(self.state(), self.state())
        other = replay(ReplayRequest(seed=43, max_rounds=10))
        self.assertNotEqual(self.state()['observation']['target_document']['your_copied_reference'], other['observation']['target_document']['your_copied_reference'])

    def test_typing_is_not_navigation_or_completion(self):
        self.until_role('auditor')
        state = self.step({'action': 'type_url', 'url': self.canonical()})
        self.assertEqual(state['outcome']['verified_repaired_reference'], 0)
        self.assertEqual(state['events'][-1]['result']['navigation_committed'], False)
        self.until_role('auditor')
        observation = self.state()['observation']
        self.assertEqual(observation['browser']['draft_url'], self.canonical())
        self.assertIsNone(observation['browser']['document_id'])
        state = self.step({'action': 'navigate'})
        self.assertEqual(state['outcome']['verified_repaired_reference'], 1)
        self.assertEqual(state['outcome']['auditor_opened_current_original'], 1)

    def test_owner_report_and_owner_open_do_not_complete(self):
        self.until_role('ethics_owner')
        state = self.step({'action': 'report_status', 'document_key': 'irb-protocol', 'status': 'completed', 'summary': 'It is fixed.'})
        self.assertEqual(state['outcome']['verified_repaired_reference'], 0)
        self.until_role('ethics_owner')
        state = self.step({'action': 'open_url', 'url': self.canonical()})
        self.assertEqual(state['outcome']['verified_repaired_reference'], 0)

    def test_next_role_and_wrong_turn(self):
        state = self.state()
        self.assertEqual(state['observation']['agent_id'], state['next_role'])
        wrong = 'auditor' if state['next_role'] == 'ethics_owner' else 'ethics_owner'
        response = self.client.post('/society/worlds/replay', json={'actions': [{'role': wrong, 'action': {'action': 'wait'}}]})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()['detail']['expected_role'], state['next_role'])

    def test_semantically_failed_tool_consumes_one_opportunity(self):
        state = self.step({'action': 'open_url', 'url': 'https://outside.invalid/not-a-proxy-document'})
        self.assertEqual(state['steps_used'], 1)
        self.assertFalse(state['events'][-1]['result']['ok'])
        self.assertEqual(state['outcome']['failed_actions'], 1)

    def test_invalid_and_oversize_request_rejected(self):
        role = self.state()['next_role']
        invalid = [
            {'seed': True}, {'seed': '42'}, {'seed': -1}, {'seed': 2**53},
            {'max_rounds': 3}, {'max_rounds': 11}, {'max_rounds': 4.0},
            {'unknown': 'not allowed'},
            {'actions': [{'role': role, 'action': {'action': 'exec', 'command': 'no'}}]},
            {'actions': [{'role': role, 'action': {'action': 'wait', 'url': 'unexpected'}}]},
            {'actions': [{'role': role, 'action': {'action': 'type_url', 'url': 'x'*1001}}]},
            {'actions': [{'role': role, 'action': {'action': 'type_url', 'url': {}}}]},
            {'actions': [{'role': role, 'action': {'action': 'wait'}}]*21},
            {'max_rounds': 4, 'actions': [{'role': role, 'action': {'action': 'wait'}}]*9},
        ]
        for body in invalid:
            with self.subTest(body=str(body)[:90]):
                response = self.client.post('/society/worlds/replay', json=body)
                self.assertEqual(response.status_code, 422, response.text)

    def test_huge_integer_and_invalid_unicode_return_validation_errors(self):
        role = self.state()['next_role']
        for value in (10**1000, "\ud800"):
            body = {'actions': [{'role': role, 'action': {'action': 'type_url', 'url': value}}]}
            response = self.client.post('/society/worlds/replay', content=json.dumps(body),
                                        headers={'content-type': 'application/json'})
            self.assertEqual(response.status_code, 422, response.text)
            self.assertNotIn('input', response.json()['detail'][0])

    def test_raw_body_limit_applies_before_json_parsing(self):
        body = b'{"actions":[],"padding":"' + b'x' * 65536 + b'"}'
        # With a normal Content-Length and with a chunked stream, the direct
        # FastAPI endpoint rejects large input without depending on a proxy.
        for content in (body, iter([body[:20000], body[20000:]])):
            response = self.client.post('/society/worlds/replay', content=content,
                                        headers={'content-type': 'application/json'})
            self.assertEqual(response.status_code, 413, response.text)
        # Malformed tiny JSON still receives an ordinary validation response.
        response = self.client.post('/society/worlds/replay', content=b'{')
        self.assertEqual(response.status_code, 422)

    def test_terminal_has_no_role_or_observation(self):
        actions = []
        for _ in range(8):
            state = replay(ReplayRequest(seed=42, max_rounds=4, actions=actions))
            actions.append({'role': state['next_role'], 'action': {'action': 'wait'}})
        state = replay(ReplayRequest(seed=42, max_rounds=4, actions=actions))
        self.assertTrue(state['terminal'])
        self.assertIsNone(state['next_role'])
        self.assertIsNone(state['observation'])
        self.assertEqual(state['outcome']['verified_repaired_reference'], 0)
        self.assertNotIn('privileged_failure_cause', str(state['observation']))


if __name__ == '__main__':
    unittest.main()
