-- Role + profile — spec §6. User login thật KHÔNG ở đây (create_users.sql.example).
CREATE ROLE IF NOT EXISTS dlck_ingester;
CREATE ROLE IF NOT EXISTS dlck_api;

-- Dây đai server-side chống nến đếm đôi khi retry (spec §5.4, đo T9)
CREATE SETTINGS PROFILE IF NOT EXISTS dlck_ingester_profile
  SETTINGS deduplicate_blocks_in_dependent_materialized_views = 1
  TO dlck_ingester;

GRANT SELECT, INSERT ON rt.* TO dlck_ingester;
GRANT SELECT ON rt.* TO dlck_api;
