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
    embedding   JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Adopt the embedding column on pre-existing schemas.
ALTER TABLE public.entries ADD COLUMN IF NOT EXISTS embedding JSONB;

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

-- ==================
--  entry_reactions  (multi-emoji counters per entry)
-- ==================
CREATE TABLE IF NOT EXISTS public.entry_reactions (
    entry_id  BIGINT  NOT NULL REFERENCES public.entries(id) ON DELETE CASCADE,
    emoji     TEXT    NOT NULL,
    count     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (entry_id, emoji)
);

CREATE INDEX IF NOT EXISTS idx_entry_reactions_entry ON public.entry_reactions(entry_id);

-- ===========
--  comments  (threaded, self-referential parent)
-- ===========
CREATE TABLE IF NOT EXISTS public.comments (
    id                BIGSERIAL PRIMARY KEY,
    entry_id          BIGINT NOT NULL REFERENCES public.entries(id)  ON DELETE CASCADE,
    parent_comment_id BIGINT          REFERENCES public.comments(id) ON DELETE CASCADE,
    author            TEXT,
    body              TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_comments_entry  ON public.comments(entry_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON public.comments(parent_comment_id);

-- ==============
--  collections  (user-named groups of entries)
-- ==============
CREATE TABLE IF NOT EXISTS public.collections (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.collection_entries (
    collection_id BIGINT NOT NULL REFERENCES public.collections(id) ON DELETE CASCADE,
    entry_id      BIGINT NOT NULL REFERENCES public.entries(id)     ON DELETE CASCADE,
    PRIMARY KEY (collection_id, entry_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_entries_entry ON public.collection_entries(entry_id);

-- =============
--  highlights  (starred entries with optional note)
-- =============
CREATE TABLE IF NOT EXISTS public.highlights (
    id          BIGSERIAL PRIMARY KEY,
    entry_id    BIGINT NOT NULL REFERENCES public.entries(id) ON DELETE CASCADE,
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_highlights_entry ON public.highlights(entry_id);

-- ==========
--  prompts  (daily prompt suggestions)
-- ==========
CREATE TABLE IF NOT EXISTS public.prompts (
    id          BIGSERIAL PRIMARY KEY,
    text        TEXT NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_prompts_active ON public.prompts(active);

-- =========================================
--  Row-Level Security
--  We're using the service_role key from the
--  server, which bypasses RLS. But Supabase
--  enables RLS by default; we leave it ON
--  and add no anon policies, so anon writes
--  are denied. The server can still do
--  everything via service_role.
-- =========================================
ALTER TABLE public.entries            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags               ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entry_tags         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmarks          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmark_tags      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.digests            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.entry_reactions    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comments           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collections        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collection_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.highlights         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prompts            ENABLE ROW LEVEL SECURITY;
