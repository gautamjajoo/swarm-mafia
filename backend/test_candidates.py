import json,tempfile,unittest
from pathlib import Path
from candidates import discover_candidates
class CandidateTests(unittest.TestCase):
 def setUp(self):
  self.dir=tempfile.TemporaryDirectory();self.path=Path(self.dir.name)/'cache.json'
  self.rows=[dict(session_id='session-a',agent_id='agent-a',actor='A',count=120,first='2025-06-01T10:00:00Z',last='2025-06-01T11:00:00Z',first_id='computer_use_turns:first',last_id='computer_use_turns:last',actions={'command':120},time_regressions=0,message_share=0,elapsed_seconds=3600,error_field_nonempty=3,longest_nontrivial_action_with_error_run=dict(action_type='command',count=3,error_present_count=3,first_id='computer_use_turns:repeat-first',last_id='computer_use_turns:repeat-last',fingerprint='abc'))]
  self.save()
 def tearDown(self):self.dir.cleanup()
 def save(self):self.path.write_text(json.dumps(dict(snapshot='pin',complete=True,scanned_turns=120,expected_turns=120,sessions=self.rows,limitations=[])))
 def call(self,**kwargs):return discover_candidates(cache_path=self.path,**kwargs)
 def test_repeated_action_is_candidate_not_failure(self):
  r=self.call(feature='repeated_action');c=r['data']['records'][0];self.assertEqual(c['source_ids'],['computer_use_turns:repeat-first','computer_use_turns:repeat-last']);self.assertEqual(c['evidence_status'],'structural_candidate');self.assertEqual(c['causal_status'],'not_established');self.assertNotIn('excerpt',c)
 def test_crossing_temporal_scope_excluded(self):
  r=self.call(from_time='2025-06-01T10:30:00Z');self.assertEqual(r['data']['records'],[]);self.assertEqual(r['coverage']['sessions_excluded_by_time_scope'],1)
 def test_timezone_scope_exact(self):self.assertTrue(self.call(from_time='2025-06-01T12:00:00+02:00')['data']['records'])
 def test_wrong_actor_excluded(self):self.assertEqual(self.call(agent_id='different')['data']['records'],[])
 def test_scope_not_silently_ignored(self):
  for opts in [dict(source='swarmtraces'),dict(table='chat_messages'),dict(feature='failure'),dict(limit=21)]:
   with self.assertRaises(ValueError):self.call(**opts)
 def test_regressing_time_not_run_evidence(self):
  self.rows[0]['time_regressions']=1;self.save();self.assertEqual(self.call(feature='repeated_action')['data']['records'],[])
 def test_tied_timestamps_do_not_establish_ordered_run(self):
  self.rows[0]['timestamp_ties']=1;self.save();self.assertEqual(self.call(feature='repeated_action')['data']['records'],[])
 def test_unavailable_cache_explicit(self):
  with self.assertRaises(RuntimeError):discover_candidates(cache_path=Path(self.dir.name)/'missing')
 def test_scalar_pool_clipping_disclosed(self):
  self.path.write_text(json.dumps(dict(snapshot='pin',complete=True,scanned_turns=120,expected_turns=120,top_sessions_by_turns=self.rows,top_nonmessage_scalar_runs=[],top_message_dominant_sessions=[],limitations=[])))
  r=self.call();self.assertEqual(r['coverage']['session_features'],'global top feature pools only');self.assertIn('strings clipped',r['data']['records'][0]['features']['fingerprint_basis'])
if __name__=='__main__':unittest.main()
