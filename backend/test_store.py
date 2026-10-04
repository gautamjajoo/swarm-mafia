import json
import os
from pathlib import Path
import tempfile
import unittest

from store import Store, initialize, normalize_time

class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name,"evidence.sqlite")
        self.db = initialize(self.path)
        for table in ("agents","computer_use_sessions","computer_use_turns","events","chat_messages"):
            self.db.execute("INSERT INTO sources(table_name,object_uri,generation,expected,indexed,status,bytes) VALUES(?,?,?,1,1,'complete',10)",(table,"gs://private/"+table,"123"))
        self.add("agents","a",None,None,"Agent A")
        self.add("computer_use_sessions","s","a",None,"A task")
        self.add("computer_use_turns","t","a","s","A repeated command failed")
        self.add("computer_use_turns","u","a","missing","Other command")
        self.db.commit()
        self.store = Store(self.path)

    def add(self, table, ident, agent, session, excerpt):
        cur=self.db.execute("INSERT INTO records(table_name,source_id,timestamp,agent_id,session_id,action_type,excerpt,excerpt_truncated,metadata,source_line,byte_offset,byte_length,row_sha256) VALUES(?,?,?,?,?,'test',?,0,'{}',1,0,10,'hash')",(table,ident,"2026-01-01T00:00:00.000000Z",agent,session,excerpt))
        self.db.execute("INSERT INTO record_fts(rowid,excerpt) VALUES(?,?)",(cur.lastrowid,excerpt))

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_full_record_provenance_and_search(self):
        result=self.store.search("repeated command",agent_id="a")
        self.assertEqual([r["id"] for r in result["data"]],["computer_use_turns:t"])
        self.assertEqual(result["data"][0]["provenance"]["generation"],"123")
        self.assertIn("not all raw content",result["coverage"]["search_scope"])

    def test_session_join_is_not_fabricated_direct_actor_edge(self):
        graph=self.store.graph("computer_use_turns:t",hops=2)
        edges=graph["data"]["edges"]
        self.assertTrue(any(e["source"]=="computer_use_turns:t" and e["target"]=="computer_use_sessions:s" for e in edges))
        self.assertFalse(any(e["source"]=="computer_use_turns:t" and e["target"]=="agents:a" for e in edges))
        self.assertTrue(any(e["source"]=="computer_use_sessions:s" and e["target"]=="agents:a" for e in edges))

    def test_graph_bound_and_unresolved(self):
        result=self.store.graph("computer_use_turns:t",hops=2,limit=1)
        self.assertEqual(len(result["data"]["nodes"]),1)
        self.assertTrue(result["truncated"])
        result=self.store.graph("computer_use_turns:u",hops=1)
        self.assertEqual(result["data"]["unresolved_references"],1)

    def test_timezone_filter_equivalence(self):
        result=self.store.search("",from_time="2026-01-01T02:00:00+02:00",to_time="2026-01-01T00:00:00Z")
        self.assertEqual(len(result["data"]),4)
        self.assertEqual(normalize_time("2026-01-01T02:00:00+02:00"),"2026-01-01T00:00:00.000000Z")

    def test_literal_search_does_not_accept_fts_or_sql_operators(self):
        self.assertEqual(self.store.search("failed OR nonexistent")["data"],[])
        self.assertEqual(self.store.search("'; DROP TABLE records; --")["data"],[])
        self.assertIsNotNone(self.store.record("agents","a"))

    def test_fts_membership_preserves_time_order_filters_and_pagination(self):
        for i in range(8):
            self.add("computer_use_turns","n"+str(i),"a" if i%2==0 else "b","s","needle")
            self.db.execute("UPDATE records SET timestamp=? WHERE source_id=?",(f"2026-01-01T00:00:{i:02d}.000000Z","n"+str(i)))
        self.db.commit()
        result=self.store.search("needle",agent_id="a",table="computer_use_turns",from_time="2026-01-01T00:00:02Z",to_time="2026-01-01T00:00:05Z",limit=1,cursor=1)
        self.assertEqual([r["source_id"] for r in result["data"]],["n2"])
        self.assertFalse(result["truncated"])

    def test_display_name_is_exact_agent_lookup_with_source_provenance(self):
        self.db.execute("UPDATE records SET metadata=? WHERE table_name='agents'",(json.dumps({"name":"Recorded agent name"}),))
        self.db.commit()
        record=self.store.record("computer_use_turns","t")["data"]
        self.assertEqual(record["actor_name"],"Recorded agent name")
        self.assertEqual(record["actor_name_provenance"]["source_record_id"],"agents:a")
        self.assertIn("computer_use_sessions",record["actor_name_provenance"]["join"])

    def test_context_stays_in_recorded_session(self):
        self.add("computer_use_turns","v","a","s","Next actual action")
        self.db.execute("UPDATE records SET timestamp='2026-01-01T00:01:00.000000Z' WHERE source_id='v'")
        self.db.commit()
        result=self.store.context("computer_use_turns:t",before=0,after=1)
        self.assertEqual([r["source_id"] for r in result["data"]["records"]],["t","v"])
        self.assertEqual(result["data"]["scope"]["kind"],"session")
        actor_result=self.store.context("computer_use_turns:t",before=0,after=25,mode="actor")
        self.assertIn("u",[r["source_id"] for r in actor_result["data"]["records"]])
        self.assertEqual(actor_result["data"]["scope"]["kind"],"actor_across_tables")

    def test_event_context_uses_event_index(self):
        for ident,index in [("e1",1),("e2",2),("e3",3)]:
            self.add("events",ident,"a",None,"Event")
            self.db.execute("UPDATE records SET metadata=? WHERE source_id=?",(json.dumps({"event_index":index}),ident))
        self.db.execute("UPDATE records SET timestamp='2025-01-01T00:00:00.000000Z' WHERE source_id='e3'")
        self.db.commit()
        result=self.store.context("events:e2",before=1,after=1)
        self.assertEqual([r["source_id"] for r in result["data"]["records"]],["e1","e2","e3"])
        self.assertEqual(result["data"]["scope"]["order"],"event_index_then_source_id")

    def test_ambiguous_sdk_key_does_not_choose_arbitrary_parent(self):
        for table in ("claude_code_sessions","claude_code_messages"):
            self.db.execute("INSERT INTO sources(table_name,object_uri,generation,expected,indexed,status,bytes) VALUES(?,?,?,1,1,'complete',10)",(table,"gs://private/"+table,"123"))
        self.add("claude_code_sessions","sdk1","a",None,"Session")
        self.add("claude_code_sessions","sdk2","a",None,"Session")
        self.add("claude_code_messages","m","a",None,"Message")
        self.db.execute("UPDATE records SET sdk_session_id='shared-key' WHERE table_name LIKE 'claude_code_%'")
        self.db.commit()
        result=self.store.graph("claude_code_messages:m",hops=1)
        edges=result["data"]["edges"]
        self.assertEqual(sum(e["type"]=="SHARES_SDK_SESSION_KEY" for e in edges),2)
        self.assertFalse(any(e["type"]=="IN_SDK_SESSION" for e in edges))
        self.assertEqual(result["data"]["ambiguous_references"],1)

if __name__ == "__main__":
    unittest.main()
