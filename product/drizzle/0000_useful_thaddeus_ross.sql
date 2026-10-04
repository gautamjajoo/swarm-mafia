CREATE TABLE `investigations` (
	`id` text PRIMARY KEY NOT NULL,
	`title` text NOT NULL,
	`source` text NOT NULL,
	`snapshot` text NOT NULL,
	`state` text NOT NULL,
	`revision` integer DEFAULT 1 NOT NULL,
	`created_at` text NOT NULL,
	`updated_at` text NOT NULL,
	`author` text NOT NULL
);
--> statement-breakpoint
CREATE INDEX `investigations_updated` ON `investigations` (`updated_at`);