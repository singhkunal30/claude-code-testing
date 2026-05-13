-- TIL Journal schema for Supabase.
-- Paste this into the SQL editor in your Supabase project and run it.
-- Safe to re-run (CREATE ... IF NOT EXISTS / DROP POLICY IF EXISTS).

-- =========
--  entries
-- =========
CREATE TABLE IF NOT EXISTS public.entries (
    id          BIGSERIAL PRIMARY KEY,
    text        TEXT NOT NULL,
    source      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_entries_created_at ON public.entries(created_at DESC);

-- ======
--  tags
-- ======
CREATE TABLE IF NOT EXISTS public.tags (
    id    BIGSERIAL PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE
);

-- ==============
--  entry_tags  (M2M)
-- ==============
CREATE TABLE IF NOT EXISTS public.entry_tags (
    entry_id  BIGINT NOT NULL REFERENCES public.entries(id) ON DELETE CASCADE,
    tag_id    BIGINT NOT NULL REFERENCES public.tags(id)    ON DELETE CASCADE,
    PRIMARY KEY (entry_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_entry_tags_tag ON public.entry_tags(tag_id);

-- ===========
--  bookmarks
-- ===========
CREATE TABLE IF NOT EXISTS public.bookmarks (
    id          BIGSERIAL PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_bookmarks_created_at ON public.bookmarks(created_at DESC);

CREATE TABLE IF NOT EXISTS public.bookmark_tags (
    bookmark_id  BIGINT NOT NULL REFERENCES public.bookmarks(id) ON DELETE CASCADE,
    tag_id       BIGINT NOT NULL REFERENCES public.tags(id)      ON DELETE CASCADE,
    PRIMARY KEY (bookmark_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_bookmark_tags_tag ON public.bookmark_tags(tag_id);

-- =========
--  digests
-- =========
CREATE TABLE IF NOT EXISTS public.digests (
    id          BIGSERIAL PRIMARY KEY,
    period      TEXT NOT NULL,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    content     TEXT NOT NULL,
    entry_ids   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================
--  Row-Level Security
--  We're using the service_role key from the
--  server, which bypasses RLS. But Supabase
--  enables RLS by default; we leave it ON
--  and add no anon policies, so anon writes
--  are denied. The server can still do
--  everything via service_role.
-- =========================================
ALTER TABLE public.entries       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entry_tags    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmarks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmark_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.digests       ENABLE ROW LEVEL SECURITY;
