import { z } from "zod";
export const stateSchema = z.object({
  pattern: z
    .object({
      id: z.string().max(250),
      rule: z.string().max(100),
      definition: z.string().max(2000),
      source_ids: z.array(z.string().max(240)).max(10),
      count: z.number().nonnegative().optional(),
      share: z.number().min(0).max(1).optional(),
      built_at: z.string().max(80).optional(),
    })
    .optional(),
  context_seed: z.string().max(240).optional(),
  context_mode: z.enum(["source", "actor"]).optional(),
  selected_id: z.string().max(240).optional(),
  graph_seed: z.string().max(240).optional(),
  tab: z.enum(["records", "graph", "timeline", "context"]).optional(),
  query: z.string().max(2000),
  filters: z.record(z.string().max(2000)).default({}),
  pins: z
    .array(
      z.object({
        id: z.string().max(240),
        excerpt: z.string().max(8000),
        provenance: z.record(z.unknown()),
        label: z.string().max(200).optional(),
        source: z.enum(["ai-village", "swarmtraces"]).optional(),
        excerpt_truncated: z.boolean().optional(),
      }),
    )
    .max(30),
  notes: z
    .array(
      z.object({
        id: z.string().max(80),
        text: z.string().max(5000),
        record_id: z.string().max(240).optional(),
        target_claim: z.string().max(1200).optional(),
        source_ids: z.array(z.string().max(240)).max(6).optional(),
        evidence_status: z.enum([
          "observation",
          "hypothesis",
          "counterevidence",
          "question",
        ]),
        review_status: z.enum(["human_note", "reviewed", "disputed"]),
        created_at: z.string().max(80),
      }),
    )
    .max(80),
  studies: z
    .array(
      z.object({
        id: z.string().max(80),
        title: z.string().max(300),
        intervention: z.string().max(3000),
        metric: z.string().max(2000),
        control: z.string().max(2000),
        guardrail: z.string().max(2000),
        status: z.literal("proposed_unrun"),
      }),
    )
    .max(20),
  messages: z
    .array(
      z.object({
        role: z.enum(["user", "assistant"]),
        content: z.string().max(16000),
        result: z.record(z.unknown()).optional(),
      }),
    )
    .max(30),
});
export const saveSchema = z.object({
  title: z.string().trim().min(1).max(180),
  source: z.enum(["ai-village", "swarmtraces"]),
  snapshot: z.string().max(200),
  state: stateSchema,
  revision: z.number().int().positive().optional(),
});
