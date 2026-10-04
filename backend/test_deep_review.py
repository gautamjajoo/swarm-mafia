import asyncio
import copy
import json
import unittest
from backend.deep_review import deep_review, Budgets, ReviewJobs, JobBusy, raw_segments


def row(ident='1',actor='a',text='The operator attempted a bounded command.'):
    return dict(id='computer_use_turns:'+ident,source_id=ident,table='computer_use_turns',agent_id=actor,timestamp='2025-01-01T12:00:00Z',excerpt=text,provenance={'sha256':'original'},evidence_status='recorded')

class Store:
    def __init__(self):self.calls=[]
    def overview(self):return {'data':{'daily_activity':[{'day':'2024-01-01','count':1},{'day':'2025-01-01','count':2},{'day':'2026-01-01','count':1}],'agent_activity':[{'agent_id':'a','count':4}]}}
    def candidates(self,**args):return {'data':{'records':[{'source_ids':['computer_use_turns:1']}],'limitations':['Ranked leads, not population frequency']},'coverage':{'complete':True,'expected_turns':4}}
    def search(self,**args):self.calls.append(args);return {'data':[row()]}
    def record(self,table,source_id):return {'data':row(source_id)}
    def raw_record(self,table,source_id,max_bytes):
        return {'data':{'id':'computer_use_turns:'+source_id,'record':row(source_id),'raw_json':json.dumps({'irrelevant':'z'*5000,'agent_action':{'command':'publish temporary artifact'},'output':'Published artifact receipt recorded.'}),'hash_verified':True,'provenance':{'sha256':'original'}}}
    def context(self,**args):return {'data':{'records':[row()]}}

class Provider:
    def __init__(self):self.prompts=[]
    async def complete(self,system,payload,max_tokens):
        self.prompts.append(copy.deepcopy(payload))
        if 'keep_indices' in payload['task']:return {'keep_indices':[0]}
        if 'Choose up to' in payload['task']:
            if len(self.prompts)==1:return {'actions':[{'tool':'raw','arguments':{'id':'computer_use_turns:1','fields':['output']},'purpose':'Check whether the attempted action has a receipt.'}]}
            return {'ready':True,'focus_ids':['computer_use_turns:1']}
        return {'findings':[{'text':'A primary output records a publication receipt; the artifact contents were not inspected.','source_ids':['computer_use_turns:1'],'quotes':[{'source_id':'computer_use_turns:1','quote':'Published artifact receipt recorded.'}],'evidence_type':'observation','evidence_kind':'receipt','category':'outcome'}]}

class DeepTests(unittest.IsolatedAsyncioTestCase):
    async def test_discovery_raw_receipt_and_exact_field_quotes(self):
        store,provider=Store(),Provider()
        result=await deep_review('Discover behavior',retrieval=store,provider=provider)
        self.assertEqual(result['status'],'ok')
        self.assertEqual(result['outcomes'][0]['quotes'][0]['field'],'output')
        self.assertTrue(result['sources'][0]['original_hash_verified'])
        self.assertFalse(result['sources'][0]['snippet_hash_verified'])
        self.assertFalse(result['coverage']['exhaustive'])
        self.assertEqual(len(store.calls),3)
        self.assertEqual({c['from_time'][:4] for c in store.calls},{'2024','2025','2026'})
        self.assertTrue(any(s.get('arguments',{}).get('fields')==['output'] for s in result['query_plan']))

    async def test_source_scope_rejects_candidate_raw(self):
        result=await deep_review('Review',context={'filters':{'agent_id':'other'}},retrieval=Store(),provider=Provider())
        self.assertEqual(result['sources'],[])
        self.assertEqual(result['status'],'insufficient_evidence')

    async def test_budget_reserves_synthesis_and_critic(self):
        result=await deep_review('Review',retrieval=Store(),provider=Provider(),budgets=Budgets(model_calls=4,retrieval_calls=8))
        self.assertLessEqual(result['coverage']['model_calls'],4)
        self.assertLessEqual(result['coverage']['retrieval_calls'],8)
        self.assertEqual(result['status'],'ok')

    async def test_failure_is_sanitized_and_job_terminal(self):
        class Broken:
            async def complete(self,*args):raise RuntimeError('private service credential')
        manager=ReviewJobs()
        job=manager.start('Review',[],{},Store(),Broken())
        await manager.jobs[job['id']]['task']
        result=manager.get(job['id'])
        self.assertEqual(result['status'],'failed')
        self.assertNotIn('private service credential',json.dumps(result))

    async def test_outcome_from_command_only_rejected(self):
        class CommandStore(Store):
            def raw_record(self,*args,**kwargs):
                result=super().raw_record(*args,**kwargs)
                result['data']['raw_json']=json.dumps({'agent_action':{'output':'Published artifact receipt recorded.'}})
                return result
        result=await deep_review('Review',retrieval=CommandStore(),provider=Provider())
        self.assertEqual(result['outcomes'],[])
        self.assertGreater(result['coverage']['rejection_reason_counts']['outcome_without_primary_receipt'],0)

    async def test_repeated_query_is_not_executed_twice(self):
        class Repeat(Provider):
            async def complete(self,system,payload,max_tokens):
                if 'Choose up to' in payload['task'] and not self.prompts:
                    self.prompts.append(copy.deepcopy(payload))
                    return {'actions':[{'tool':'search','arguments':{'q':'receipt'}}]*4}
                return await super().complete(system,payload,max_tokens)
        store=Store()
        result=await deep_review('Review',retrieval=store,provider=Repeat())
        self.assertEqual(len([c for c in store.calls if c['q']=='receipt']),1)
        self.assertTrue(any(s['status']=='rejected' for s in result['query_plan']))

    async def test_lexical_budget_reserves_primary_verification(self):
        class Searching(Provider):
            async def complete(self,system,payload,max_tokens):
                if 'Choose up to' in payload['task']:
                    self.prompts.append(copy.deepcopy(payload))
                    n=len(self.prompts)
                    return {'actions':[{'tool':'search','arguments':{'q':f'term{n}-{i}'}} for i in range(4)],'focus_ids':['computer_use_turns:1']}
                return await super().complete(system,payload,max_tokens)
        result=await deep_review('Review',retrieval=Store(),provider=Searching())
        self.assertTrue(result['coverage']['verification_phase_attempted'])
        self.assertGreater(result['coverage']['primary_raw_records_inspected'],0)
        self.assertLessEqual(result['coverage']['retrieval_calls'],32)
        self.assertLessEqual(result['coverage']['search_queries_executed'],15)
        self.assertEqual(result['review_status'],'action_evidence_reviewed')

    async def test_raw_upgrade_evicts_nominations_within_byte_budget(self):
        class Crowded(Store):
            def search(self,**args):return {'data':[row(str(i),text='nomination '*170) for i in range(1,4)]}
            def raw_record(self,*args,**kwargs):
                r=super().raw_record(*args,**kwargs)
                r['data']['raw_json']=json.dumps({'agent_action':{'command':'a'*2000},'output':'b'*3000,'error':'c'*2000})
                return r
        result=await deep_review('Review',retrieval=Crowded(),provider=Provider(),budgets=Budgets(retained_bytes=12000))
        self.assertGreater(result['coverage']['primary_raw_records_inspected'],0)
        self.assertGreater(result['coverage']['excluded_source_reason_counts'].get('nomination_evicted_for_primary_fields',0),0)
        self.assertLessEqual(result['coverage']['retained_evidence_bytes'],12000)

    async def test_repeated_raw_and_context_reads_are_deduplicated(self):
        class Duplicate(Provider):
            async def complete(self,system,payload,max_tokens):
                if 'Choose up to' in payload['task'] and not self.prompts:
                    self.prompts.append(copy.deepcopy(payload))
                    return {'actions':[{'tool':'raw','arguments':{'id':'computer_use_turns:1'}}]*4}
                return await super().complete(system,payload,max_tokens)
        result=await deep_review('Review',retrieval=Store(),provider=Duplicate())
        self.assertEqual(len([s for s in result['query_plan'] if s['action']=='raw' and s['status']=='completed']),1)
        self.assertEqual(len([s for s in result['query_plan'] if s['action']=='raw' and s['status']=='rejected']),3)

    async def test_repeat_claim_requires_distinct_primary_turns(self):
        class Repeated(Provider):
            async def complete(self,*args):
                r=await super().complete(*args)
                if r.get('findings'):r['findings'][0]['text']='Repeated attempts published the artifact.'
                return r
        result=await deep_review('Review',retrieval=Store(),provider=Repeated())
        self.assertEqual(result['findings'],[])
        self.assertGreater(result['coverage']['rejection_reason_counts']['sequence_claim_without_two_primary_turns'],0)

    def test_raw_beyond_first_excerpt_and_secret_redaction(self):
        segments,status=raw_segments({'data':{'raw_json':json.dumps({'padding':'x'*8000,'agent_action':{'command':'request'},'output':'visible receipt','api_key':'sk-secretplaceholder000000000000000'}),'hash_verified':True}},['output'])
        self.assertEqual(segments[0]['text'],'visible receipt')
        self.assertNotIn('sk-secret',json.dumps(segments))
        self.assertTrue(status['original_hash_verified'])
        self.assertFalse(status['snippet_hash_verified'])

if __name__=='__main__':unittest.main()
