import { sqliteTable, text, integer, index } from "drizzle-orm/sqlite-core";
export const investigations = sqliteTable(
  "investigations",
  {
    id: text("id").primaryKey(),
    title: text("title").notNull(),
    source: text("source").notNull(),
    snapshot: text("snapshot").notNull(),
    state: text("state").notNull(),
    revision: integer("revision").notNull().default(1),
    createdAt: text("created_at").notNull(),
    updatedAt: text("updated_at").notNull(),
    author: text("author").notNull(),
  },
  (t) => [index("investigations_updated").on(t.updatedAt)],
);
