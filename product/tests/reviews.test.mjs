import {test} from 'node:test';
import assert from 'node:assert/strict';
import {followReview} from '../lib/reviews.ts';
const step={step:1,action:'context',reason:'Check what happened after the correction',summary:'Retrieved six records',status:'completed'};
const initial={id:'job-1',status:'running',progress:[]};
const result={status:'ok',answer:'A bounded finding',findings:[],sources:[],coverage:{exhaustive:false}};
test('review follows same job and retains the actual retrieval trail with result',async()=>{
 const updates=[];const calls=[];
 const answer=await followReview(initial,new AbortController().signal,j=>updates.push(j.status),async id=>{calls.push(id);return {id,status:'completed',progress:[step],result};},1);
 assert.deepEqual(calls,['job-1']);assert.deepEqual(updates,['running','completed']);assert.deepEqual(answer.progress,[step]);assert.equal(answer.coverage.exhaustive,false);
});
test('failed jobs do not become empty successful reports',async()=>{
 await assert.rejects(followReview({...initial,status:'failed',error:'Provider unavailable'},new AbortController().signal,()=>{},async()=>{throw new Error('should not poll');},1),/Provider unavailable/);
});
test('cancelled signal never polls or exposes a completed late response',async()=>{
 const controller=new AbortController();controller.abort();let polls=0;
 await assert.rejects(followReview(initial,controller.signal,()=>{},async()=>{polls++;return {...initial,status:'completed',result};},1),{name:'AbortError'});
 assert.equal(polls,0);
});
test('in-flight cancellation stops subsequent polls',async()=>{
 const controller=new AbortController();let calls=0;
 await assert.rejects(followReview(initial,controller.signal,()=>{},async()=>{calls++;controller.abort();return {...initial,status:'completed',result};},1),{name:'AbortError'});
 assert.equal(calls,1);
});
test('malformed completion remains an error with the question recoverable',async()=>{
 await assert.rejects(followReview({...initial,status:'completed'},new AbortController().signal,()=>{},async()=>initial,1),/without a result/);
});
