import test from 'node:test';
import assert from 'node:assert/strict';
import { rubricPresets, withBehaviorRubric } from '../lib/behavior-rubric.ts';
test('a custom behavioral rubric reaches the actual question with evidence and observability limits', () => {
  const rubric = { ...rubricPresets[0], evidence: 'Check the recipient-visible artifact, not the acknowledgment.' };
  const prompt = withBehaviorRubric('Did the correction change the output?', rubric);
  assert.ok(prompt.startsWith('Did the correction change the output?'));
  assert.ok(prompt.includes(rubric.evidence));
  assert.ok(prompt.includes(rubric.opportunity));
  assert.ok(prompt.includes(rubric.counterevidence));
  assert.ok(prompt.includes('not assessable'));
});
test('removing a rubric removes the criteria and excessive combined questions are rejected without truncation', () => {
  assert.equal(withBehaviorRubric('  Show a handoff.  ', null), 'Show a handoff.');
  assert.throws(() => withBehaviorRubric('x'.repeat(3800), rubricPresets[0]), /4,000/);
});
