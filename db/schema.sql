CREATE TABLE IF NOT EXISTS posts (
    id                   INTEGER PRIMARY KEY,
    fb_post_id           TEXT UNIQUE NOT NULL,
    post_url             TEXT NOT NULL,
    page_name            TEXT NOT NULL DEFAULT 'BANHAOSTATION',
    posted_at            TIMESTAMP,
    scraped_at           TIMESTAMP NOT NULL,
    image_url            TEXT,
    image_local_path     TEXT,
    image_sha256         TEXT,
    caption_raw          TEXT,
    status                TEXT NOT NULL DEFAULT 'pending'
                           CHECK (status IN ('pending', 'candidate', 'vision_processed',
                                              'not_result_board', 'error')),
    vision_processed_at   TIMESTAMP,
    vision_raw_response   TEXT,
    error_message         TEXT
);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_image_sha256 ON posts(image_sha256);

CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY,
    post_id         INTEGER NOT NULL UNIQUE REFERENCES posts(id),
    venue           TEXT,
    event_date_raw  TEXT,
    event_date      DATE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rocket_results (
    id                       INTEGER PRIMARY KEY,
    event_id                 INTEGER NOT NULL REFERENCES events(id),
    rocket_name_raw          TEXT NOT NULL,
    rocket_name_normalized   TEXT NOT NULL,
    metric_a                 INTEGER,
    metric_b                 INTEGER,
    metric_category_text     TEXT,
    achieved_raw             TEXT,
    achieved_value           INTEGER,
    tie_band_low              INTEGER,
    tie_band_high              INTEGER,
    computed_outcome            TEXT CHECK (computed_outcome IN ('win', 'loss', 'tie')),
    outcome_icon                 TEXT NOT NULL CHECK (outcome_icon IN ('win', 'loss', 'tie')),
    outcome                       TEXT NOT NULL CHECK (outcome IN ('win', 'loss', 'tie')),
    outcome_mismatch                BOOLEAN NOT NULL DEFAULT 0,
    is_champion                      BOOLEAN NOT NULL DEFAULT 0,
    created_at                        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rocket_results_name ON rocket_results(rocket_name_normalized);
CREATE INDEX IF NOT EXISTS idx_rocket_results_event ON rocket_results(event_id);

CREATE TABLE IF NOT EXISTS scrape_runs (
    id                          INTEGER PRIMARY KEY,
    started_at                  TIMESTAMP NOT NULL,
    finished_at                 TIMESTAMP,
    posts_scanned                INTEGER DEFAULT 0,
    posts_new                    INTEGER DEFAULT 0,
    vision_calls_made             INTEGER DEFAULT 0,
    vision_calls_skipped_cache     INTEGER DEFAULT 0,
    errors_count                    INTEGER DEFAULT 0
);

DROP VIEW IF EXISTS v_rocket_stats;
CREATE VIEW v_rocket_stats AS
SELECT
    rocket_name_normalized AS rocket_name,
    COUNT(*) AS races,
    SUM(CASE WHEN outcome = 'win'  THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN outcome = 'loss' THEN 1 ELSE 0 END) AS losses,
    SUM(CASE WHEN outcome = 'tie'  THEN 1 ELSE 0 END) AS ties,
    SUM(CASE WHEN is_champion = 1  THEN 1 ELSE 0 END) AS championships,
    ROUND(1.0 * SUM(CASE WHEN outcome = 'win' THEN 1 ELSE 0 END) / COUNT(*), 4) AS win_rate
FROM rocket_results
GROUP BY rocket_name_normalized;
