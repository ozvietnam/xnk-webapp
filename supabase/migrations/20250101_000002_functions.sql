-- ============================================================
-- XNK Webapp — Functions & Triggers (separate migration)
-- Runs after 000001 tables are created.
-- rollback: DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE; DROP FUNCTION IF EXISTS search_hs_codes(TEXT, INTEGER, FLOAT) CASCADE;
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

CREATE OR REPLACE FUNCTION search_hs_codes(
    search_query    TEXT,
    result_limit    INTEGER DEFAULT 20,
    sim_threshold   REAL    DEFAULT 0.15
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
