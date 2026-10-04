import unittest
from patterns import discover_exact_repetitions, participation_candidates

LONG="This is a recorded message long enough to qualify for the exact lexical repetition candidate rule."

def row(i,text=LONG,clipped=0,actor="a"):
    return {"source_id":str(i),"agent_id":actor,"timestamp":"2026-01-01T00:00:00.000000Z","excerpt":text,"excerpt_truncated":clipped,"metadata":{}}

class PatternTests(unittest.TestCase):
    def test_case_and_whitespace_repeat_has_actual_evidence_and_no_causal_flag(self):
        patterns,coverage=discover_exact_repetitions([row(1),row(2,LONG.upper(),actor="b"),row(3,LONG.replace(" ","  \n"))])
        self.assertEqual(len(patterns),1)
        p=patterns[0]
        self.assertEqual(p["count"],3)
        self.assertEqual(p["actor_count"],2)
        self.assertEqual(p["source_ids"],["chat_messages:1","chat_messages:2","chat_messages:3"])
        self.assertFalse(p["causal_claim"])
        self.assertEqual(p["evidence_status"],"lexical_candidate")
        self.assertEqual(coverage["eligible_chat_records"],3)

    def test_clipped_prefix_cannot_create_false_repeat(self):
        patterns,coverage=discover_exact_repetitions([row(1),row(2),row(3,clipped=1)])
        self.assertEqual(patterns,[])
        self.assertEqual(coverage["eligible_chat_records"],2)

    def test_short_or_nonidentical_messages_do_not_qualify(self):
        rows=[row(i,"yes") for i in range(10)]+[row(11),row(12,LONG+" More.")]
        self.assertEqual(discover_exact_repetitions(rows)[0],[])

    def test_unknown_actors_not_invented_and_samples_bounded(self):
        patterns,_=discover_exact_repetitions([row(i,actor=None) for i in range(20)])
        self.assertEqual(patterns[0]["actor_count"],0)
        self.assertEqual(patterns[0]["unknown_actor_occurrences"],20)
        self.assertEqual(len(patterns[0]["source_ids"]),10)

    def test_samples_span_earliest_and_latest_even_when_input_is_reversed(self):
        rows=[]
        for i in reversed(range(20)):
            r=row(i)
            r["timestamp"]=f"2026-01-01T00:00:{i:02d}.000000Z"
            rows.append(r)
        patterns,_=discover_exact_repetitions(rows)
        self.assertEqual(patterns[0]["source_ids"],["chat_messages:"+str(i) for i in list(range(5))+list(range(15,20))])
        self.assertEqual(patterns[0]["count"],20)

    def test_participation_denominator_excludes_human_unknown_and_other_rooms(self):
        rows=[]
        for i in range(30):
            r=row(i,actor="a" if i<20 else "b")
            r.update(room_id="room1",metadata={"speaker_type":"agent"})
            rows.append(r)
        for i in range(5):
            r=row(100+i,actor=None)
            r.update(room_id="room1",metadata={"speaker_type":"user"})
            rows.append(r)
        r=row(200,actor=None)
        r.update(room_id="room1",metadata={"speaker_type":"agent"})
        rows.append(r)
        for i in range(10):
            r=row(300+i,actor="c")
            r.update(room_id="room2",metadata={"speaker_type":"agent"})
            rows.append(r)
        tracker={"buckets":{},"excluded_missing_room_or_time":0}
        discover_exact_repetitions(rows,tracker)
        candidates=participation_candidates(tracker)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["message_count"],20)
        self.assertEqual(candidates[0]["eligible_agent_messages"],30)
        self.assertAlmostEqual(candidates[0]["share"],2/3)
        self.assertEqual(candidates[0]["human_messages"],5)
        self.assertEqual(candidates[0]["unknown_agent_messages"],1)
        self.assertFalse(candidates[0]["causal_claim"])

if __name__=="__main__":
    unittest.main()
