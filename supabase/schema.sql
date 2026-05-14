-- TIL Journal schema for Supabase.
-- Paste this into the SQL editor in your Supabase project and run it.
-- Safe to re-run (CREATE ... IF NOT EXISTS / DROP POLICY IF EXISTS / ADD COLUMN IF NOT EXISTS).
--
-- Multi-tenancy: every resource carries a user_id referencing auth.users(id).
-- Server-side code currently uses the service_role key (RLS bypass) and
-- enforces tenancy at the application layer; the RLS policies below are in
-- place so the schema is correct when the server switches to per-request
-- user JWTs (Phase 2).

-- =========
--  entries
-- =========
CREATE TABLE IF NOT EXISTS public.entries (
    id           BIGSERIAL PRIMARY KEY,
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    text         TEXT NOT NULL,
    source       TEXT,
    embedding    JSONB,
    share_token  TEXT UNIQUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.entries ADD COLUMN IF NOT EXISTS user_id     UUID REFERENCES auth.users(id) ON DELETE CASCADE;
ALTER TABLE public.entries ADD COLUMN IF NOT EXISTS embedding   JSONB;
ALTER TABLE public.entries ADD COLUMN IF NOT EXISTS share_token TEXT UNIQUE;

CREATE INDEX IF NOT EXISTS idx_entries_user_created ON public.entries(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entries_share_token  ON public.entries(share_token);

-- ======
--  tags  (per-user; the same name can exist for different users)
-- ======
CREATE TABLE IF NOT EXISTS public.tags (
    id       BIGSERIAL PRIMARY KEY,
    user_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name     TEXT NOT NULL
);

ALTER TABLE public.tags ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_tags_user_name ON public.tags(user_id, name);

-- ==============
--  entry_tags  (M2M; tenancy derived through parent rows)
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
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    title       TEXT,
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.bookmarks ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_bookmarks_user_created ON public.bookmarks(user_id, created_at DESC);

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
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    period      TEXT NOT NULL,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    content     TEXT NOT NULL,
    entry_ids   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.digests ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- ==================
--  entry_reactions
-- ==================
CREATE TABLE IF NOT EXISTS public.entry_reactions (
    entry_id  BIGINT  NOT NULL REFERENCES public.entries(id) ON DELETE CASCADE,
    emoji     TEXT    NOT NULL,
    count     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (entry_id, emoji)
);

CREATE INDEX IF NOT EXISTS idx_entry_reactions_entry ON public.entry_reactions(entry_id);

-- ===========
--  comments
-- ===========
CREATE TABLE IF NOT EXISTS public.comments (
    id                BIGSERIAL PRIMARY KEY,
    user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    entry_id          BIGINT NOT NULL REFERENCES public.entries(id)  ON DELETE CASCADE,
    parent_comment_id BIGINT          REFERENCES public.comments(id) ON DELETE CASCADE,
    author            TEXT,
    body              TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.comments ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_comments_entry  ON public.comments(entry_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent ON public.comments(parent_comment_id);

-- ==============
--  collections
-- ==============
CREATE TABLE IF NOT EXISTS public.collections (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.collections ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;
CREATE UNIQUE INDEX IF NOT EXISTS uq_collections_user_name ON public.collections(user_id, name);

CREATE TABLE IF NOT EXISTS public.collection_entries (
    collection_id BIGINT NOT NULL REFERENCES public.collections(id) ON DELETE CASCADE,
    entry_id      BIGINT NOT NULL REFERENCES public.entries(id)     ON DELETE CASCADE,
    PRIMARY KEY (collection_id, entry_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_entries_entry ON public.collection_entries(entry_id);

-- =============
--  highlights
-- =============
CREATE TABLE IF NOT EXISTS public.highlights (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    entry_id    BIGINT NOT NULL REFERENCES public.entries(id) ON DELETE CASCADE,
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.highlights ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_highlights_entry ON public.highlights(entry_id);

-- ==========
--  prompts
-- ==========
CREATE TABLE IF NOT EXISTS public.prompts (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.prompts ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_prompts_active ON public.prompts(active);

-- =========================================
--  Row-Level Security
--  Phase 1: server uses service_role and bypasses RLS; tenancy is enforced
--  in application code. The policies below are correct for Phase 2, where
--  the server switches to per-request user JWTs and PostgREST evaluates
--  auth.uid() against the row.
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

-- Owner-only policies for resource tables (Phase 2 enforcement).
DROP POLICY IF EXISTS owner_all ON public.entries;
CREATE POLICY owner_all ON public.entries
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS owner_all ON public.tags;
CREATE POLICY owner_all ON public.tags
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS owner_all ON public.bookmarks;
CREATE POLICY owner_all ON public.bookmarks
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS owner_all ON public.digests;
CREATE POLICY owner_all ON public.digests
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS owner_all ON public.comments;
CREATE POLICY owner_all ON public.comments
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS owner_all ON public.collections;
CREATE POLICY owner_all ON public.collections
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS owner_all ON public.highlights;
CREATE POLICY owner_all ON public.highlights
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS owner_all ON public.prompts;
CREATE POLICY owner_all ON public.prompts
    USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Junction-table policies: tenancy via parent.
DROP POLICY IF EXISTS owner_all ON public.entry_tags;
CREATE POLICY owner_all ON public.entry_tags
    USING (EXISTS (SELECT 1 FROM public.entries e WHERE e.id = entry_tags.entry_id AND e.user_id = auth.uid()))
    WITH CHECK (EXISTS (SELECT 1 FROM public.entries e WHERE e.id = entry_tags.entry_id AND e.user_id = auth.uid()));

DROP POLICY IF EXISTS owner_all ON public.bookmark_tags;
CREATE POLICY owner_all ON public.bookmark_tags
    USING (EXISTS (SELECT 1 FROM public.bookmarks b WHERE b.id = bookmark_tags.bookmark_id AND b.user_id = auth.uid()))
    WITH CHECK (EXISTS (SELECT 1 FROM public.bookmarks b WHERE b.id = bookmark_tags.bookmark_id AND b.user_id = auth.uid()));

DROP POLICY IF EXISTS owner_all ON public.entry_reactions;
CREATE POLICY owner_all ON public.entry_reactions
    USING (EXISTS (SELECT 1 FROM public.entries e WHERE e.id = entry_reactions.entry_id AND e.user_id = auth.uid()))
    WITH CHECK (EXISTS (SELECT 1 FROM public.entries e WHERE e.id = entry_reactions.entry_id AND e.user_id = auth.uid()));

DROP POLICY IF EXISTS owner_all ON public.collection_entries;
CREATE POLICY owner_all ON public.collection_entries
    USING (EXISTS (SELECT 1 FROM public.collections c WHERE c.id = collection_entries.collection_id AND c.user_id = auth.uid()))
    WITH CHECK (EXISTS (SELECT 1 FROM public.collections c WHERE c.id = collection_entries.collection_id AND c.user_id = auth.uid()));

-- Public read for shared entries (Phase 2): a row is readable by anyone if
-- share_token is non-null. We don't implement this in app code yet, but the
-- policy is here so the share view will work once the server hands off to
-- the anon role for /share/* routes.
DROP POLICY IF EXISTS public_shared_read ON public.entries;
CREATE POLICY public_shared_read ON public.entries
    FOR SELECT USING (share_token IS NOT NULL);
