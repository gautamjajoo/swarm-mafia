"""Integrity checks for the report evidence graph and assessability contract."""
import json,re,unittest
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2]
C=json.loads((ROOT/'product/data/report-catalog.json').read_text())
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
class CatalogIntegrity(unittest.TestCase):
 def test_unique_reports_and_dimensions(self):
  self.assertEqual(len({r['id'] for r in C['reports']}),4)
  self.assertEqual({d['id'] for d in C['rubric']},{'C'+str(n) for n in range(1,9)})
 def test_chronological_anchored_source_pointers(self):
  for r in C['reports']:
   times=[dt(e['timestamp']) for e in r['timeline']];self.assertEqual(times,sorted(times));self.assertGreaterEqual(min(times),dt(r['from']));self.assertLessEqual(max(times),dt(r['to']))
   self.assertEqual(len({e['id'] for e in r['timeline']}),len(r['timeline']))
   for e in r['timeline']:
    p=e['provenance'];self.assertEqual(p['snapshot'],r['snapshot']);self.assertRegex(p['sha256'],r'^[a-f0-9]{64}$');self.assertTrue(p['object_uri'].startswith('gs://kairosity-ai-village-504821/ai-village/'));self.assertTrue(str(p['generation']).isdigit());self.assertGreater(p['line'],0);self.assertGreaterEqual(p['byte_offset'],0);self.assertGreater(p['byte_length'],0);self.assertTrue(e['raw_hash_verified']);self.assertTrue(e['quote'].strip())
 def test_no_dangling_claim_or_assessment_edges(self):
  for r in C['reports']:
   ids={e['id'] for e in r['timeline']}
   for c in r['claims']:
    self.assertTrue(c['support']);self.assertTrue(set(c['support']+c['counterevidence'])<=ids);self.assertIn(c['kind'],['observation','interpretation']);self.assertTrue(c['limit'])
   for a in r['assessments']:
    self.assertTrue(set(a['evidence_ids'])<=ids);self.assertIn(a['dimension_id'],{d['id'] for d in C['rubric']})
 def test_missing_evidence_never_becomes_a_verdict(self):
  for r in C['reports']:
   for a in r['assessments']:
    self.assertIn(a['assessment'],['consistent','inconsistent','mixed','not_assessable'])
    if a['assessment']!='not_assessable':self.assertEqual((a['opportunity'],a['observability']),('present','sufficient'))
    self.assertTrue(a['denominator']);self.assertTrue(a['rationale'])
 def test_report_provenance_not_imported_by_client_components(self):
  for p in list((ROOT/'product/components').rglob('*.tsx'))+[ROOT/'product/app/page.tsx']:
   self.assertNotIn('report-catalog',p.read_text())
if __name__=='__main__':unittest.main()
