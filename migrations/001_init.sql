-- 001_init.sql: foundation tables (users, audit log, notifications).
--
-- RULES FOR MIGRATIONS
--   * Never edit a file after it has been applied: add a new numbered file instead.
--   * Name files NNN_short_name.sql (lowercase). Agree the next number in the group chat.
--   * Each developer adds their own tables in their own file, for example 002_stock.sql.

CREATE TABLE users (
    id              SERIAL       PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    full_name       VARCHAR(100) NOT NULL,
    password_hash   TEXT         NOT NULL,
    role            VARCHAR(30)  NOT NULL
        CHECK (role IN ('counter_assistant', 'stock_manager', 'finance_manager',
                        'lead_pharmacist', 'system_manager')),
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    failed_attempts INTEGER      NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Who did what, and when. Rows can be added but never changed or deleted.
CREATE TABLE audit_log (
    id          BIGSERIAL    PRIMARY KEY,
    occurred_at TIMESTAMPTZ  NOT NULL DEFAULT now(),
    user_id     INTEGER      REFERENCES users (id),
    username    VARCHAR(50)  NOT NULL,
    action      VARCHAR(60)  NOT NULL,
    entity      VARCHAR(60),
    entity_id   VARCHAR(60),
    details     TEXT
);

CREATE INDEX audit_log_occurred_at_idx ON audit_log (occurred_at DESC);
CREATE INDEX audit_log_username_idx    ON audit_log (username);
CREATE INDEX audit_log_action_idx      ON audit_log (action);

CREATE FUNCTION audit_log_block_changes() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'The audit log cannot be changed or deleted';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_log_no_update_delete
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION audit_log_block_changes();

-- A notification goes to one user, or to everyone with a role (or both).
CREATE TABLE notifications (
    id                SERIAL       PRIMARY KEY,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    recipient_user_id INTEGER      REFERENCES users (id),
    recipient_role    VARCHAR(30),
    title             VARCHAR(120) NOT NULL,
    message           TEXT         NOT NULL,
    entity            VARCHAR(60),
    entity_id         VARCHAR(60),
    CHECK (recipient_user_id IS NOT NULL OR recipient_role IS NOT NULL)
);

CREATE INDEX notifications_role_idx ON notifications (recipient_role);
CREATE INDEX notifications_user_idx ON notifications (recipient_user_id);

-- Read state is kept per person, so one pharmacist reading a role-wide
-- notification does not mark it read for everyone else.
CREATE TABLE notification_reads (
    notification_id INTEGER     NOT NULL REFERENCES notifications (id) ON DELETE CASCADE,
    user_id         INTEGER     NOT NULL REFERENCES users (id),
    read_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (notification_id, user_id)
);
