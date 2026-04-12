-- ============================================================
-- XNK Webapp — T02: Full Database Schema
-- Migration: 20250101_000001_hs_code_schema.sql
-- ============================================================
-- rollback: DROP TABLE IF EXISTS search_history, user_profiles, customs_regulations, hs_codes, hs_chapters, hs_sections CASCADE; DROP EXTENSION IF EXISTS pg_trgm;

-- ── Extensions ───────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── hs_sections (Phần/Section của biểu thuế) ────────────────
CREATE TABLE IF NOT EXISTS hs_sections (
    section_code    VARCHAR(5)   PRIMARY KEY,
    title_vi        TEXT         NOT NULL,
    title_en        TEXT,
    chapter_range   VARCHAR(20),  -- e.g. "01-05"
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ── hs_chapters (Chương) ────────────────────────────────────
CREATE TABLE IF NOT EXISTS hs_chapters (
    chapter_code    VARCHAR(2)   PRIMARY KEY,
    section_code    VARCHAR(5)   REFERENCES hs_sections(section_code),
    title_vi        TEXT         NOT NULL,
    title_en        TEXT,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ── hs_codes (Mã HS — bảng trung tâm) ──────────────────────
CREATE TABLE IF NOT EXISTS hs_codes (
    id                      UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    code                    VARCHAR(10)  UNIQUE NOT NULL,
    chapter_code            VARCHAR(2)   REFERENCES hs_chapters(chapter_code),
    description_vi          TEXT         NOT NULL,
    description_en          TEXT,
    unit                    VARCHAR(20),
    tax_rate_normal         DECIMAL(5,2),   -- Thuế MFN (%)
    tax_rate_preferential   DECIMAL(5,2),   -- Thuế ACFTA/RCEP ưu đãi (%)
    tax_rate_special        DECIMAL(5,2),   -- Thuế đặc biệt/tự vệ (%)
    notes                   TEXT,
    is_active               BOOLEAN      DEFAULT TRUE,
    created_at              TIMESTAMPTZ  DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  DEFAULT NOW()
);

-- ── customs_regulations (Quy định hải quan) ─────────────────
CREATE TABLE IF NOT EXISTS customs_regulations (
    id                  UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    category            VARCHAR(50),  -- e.g. 'thu-tuc', 'chung-tu', 'thue', 'kiem-tra'
    title               TEXT         NOT NULL,
    content_vi          TEXT,
    effective_date      DATE,
    source_document     VARCHAR(200),
    tags                JSONB        DEFAULT '[]',
    is_active           BOOLEAN      DEFAULT TRUE,
    created_at          TIMESTAMPTZ  DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  DEFAULT NOW()
);

-- ── search_history (Lịch sử tra cứu) ───────────────────────
CREATE TABLE IF NOT EXISTS search_history (
    id              UUID         PRIMARY KEY DEFAULT uuid_generate_v4(),
    query           TEXT         NOT NULL,
    result_codes    JSONB        DEFAULT '[]',
    user_id         UUID         REFERENCES auth.users(id) ON DELETE SET NULL,
    user_session    VARCHAR(100),
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ── user_profiles (Hồ sơ người dùng) ────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    id              UUID         PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email           VARCHAR(255),
    company_name    VARCHAR(255),
    role            VARCHAR(20)  DEFAULT 'staff' CHECK (role IN ('admin', 'staff')),
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

-- GIN index cho pg_trgm similarity search trên description_vi (chính)
CREATE INDEX IF NOT EXISTS idx_hs_codes_description_vi_trgm
    ON hs_codes USING GIN (description_vi gin_trgm_ops);

-- GIN index trên description_en (phụ)
CREATE INDEX IF NOT EXISTS idx_hs_codes_description_en_trgm
    ON hs_codes USING GIN (description_en gin_trgm_ops);

-- B-tree index cho exact code lookup
CREATE INDEX IF NOT EXISTS idx_hs_codes_code
    ON hs_codes (code);

-- Index cho chapter lookup
CREATE INDEX IF NOT EXISTS idx_hs_codes_chapter
    ON hs_codes (chapter_code);

-- Index cho search_history user queries
CREATE INDEX IF NOT EXISTS idx_search_history_user_id
    ON search_history (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_search_history_session
    ON search_history (user_session, created_at DESC);

-- GIN index cho regulations tags search
CREATE INDEX IF NOT EXISTS idx_regulations_tags
    ON customs_regulations USING GIN (tags);

-- Index cho regulations category filter
CREATE INDEX IF NOT EXISTS idx_regulations_category
    ON customs_regulations (category, is_active);

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_hs_codes_updated_at
    BEFORE UPDATE ON hs_codes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER trigger_regulations_updated_at
    BEFORE UPDATE ON customs_regulations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE OR REPLACE TRIGGER trigger_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

-- hs_codes: public read, no write via API (managed via migrations)
ALTER TABLE hs_codes ENABLE ROW LEVEL SECURITY;
CREATE POLICY "hs_codes_public_read" ON hs_codes
    FOR SELECT USING (is_active = TRUE);

-- hs_chapters: public read
ALTER TABLE hs_chapters ENABLE ROW LEVEL SECURITY;
CREATE POLICY "hs_chapters_public_read" ON hs_chapters
    FOR SELECT USING (TRUE);

-- hs_sections: public read
ALTER TABLE hs_sections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "hs_sections_public_read" ON hs_sections
    FOR SELECT USING (TRUE);

-- customs_regulations: public read
ALTER TABLE customs_regulations ENABLE ROW LEVEL SECURITY;
CREATE POLICY "regulations_public_read" ON customs_regulations
    FOR SELECT USING (is_active = TRUE);

-- search_history: users see only their own records
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "search_history_own_read" ON search_history
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "search_history_insert" ON search_history
    FOR INSERT WITH CHECK (TRUE);  -- service_role handles inserts

-- user_profiles: users see/edit only their own
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "user_profiles_own_read" ON user_profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "user_profiles_own_update" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- ============================================================
-- pg_trgm SEARCH FUNCTION
-- Used by T04 hs_search service
-- ============================================================

CREATE OR REPLACE FUNCTION search_hs_codes(
    search_query    TEXT,
    result_limit    INTEGER DEFAULT 20,
    sim_threshold   FLOAT   DEFAULT 0.15
)
RETURNS TABLE (
    id                      UUID,
    code                    VARCHAR,
    description_vi          TEXT,
    description_en          TEXT,
    unit                    VARCHAR,
    tax_rate_normal         DECIMAL,
    tax_rate_preferential   DECIMAL,
    tax_rate_special        DECIMAL,
    notes                   TEXT,
    similarity_score        FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        h.id,
        h.code,
        h.description_vi,
        h.description_en,
        h.unit,
        h.tax_rate_normal,
        h.tax_rate_preferential,
        h.tax_rate_special,
        h.notes,
        GREATEST(
            similarity(h.description_vi, search_query),
            similarity(h.code, search_query)
        ) AS similarity_score
    FROM hs_codes h
    WHERE
        h.is_active = TRUE
        AND (
            similarity(h.description_vi, search_query) > sim_threshold
            OR h.description_vi ILIKE '%' || search_query || '%'
            OR h.code ILIKE search_query || '%'
        )
    ORDER BY similarity_score DESC, h.code ASC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE;
