-- ============================================================
-- XNK Webapp — Add unaccent support for diacritic-insensitive search
-- Fixes: "dien thoai" not matching "Điện thoại" in pg_trgm and ILIKE
-- rollback: DROP EXTENSION IF EXISTS unaccent; (drops the function too, recreate from 000002)
-- ============================================================

-- Enable unaccent extension (idempotent)
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Update search function to use unaccent on both sides
CREATE OR REPLACE FUNCTION search_hs_codes(
    search_query    TEXT,
    result_limit    INTEGER DEFAULT 20,
    sim_threshold   REAL    DEFAULT 0.10
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
    similarity_score        REAL
) AS $$
DECLARE
    norm_query TEXT := unaccent(lower(search_query));
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
            similarity(unaccent(lower(h.description_vi)), norm_query),
            similarity(h.code, search_query)
        ) AS similarity_score
    FROM hs_codes h
    WHERE
        h.is_active = TRUE
        AND (
            similarity(unaccent(lower(h.description_vi)), norm_query) > sim_threshold
            OR unaccent(lower(h.description_vi)) ILIKE '%' || norm_query || '%'
            OR h.code ILIKE search_query || '%'
        )
    ORDER BY similarity_score DESC, h.code ASC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql STABLE;
