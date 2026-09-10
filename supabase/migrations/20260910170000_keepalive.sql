
-- ============================================================================
-- KEEP-ALIVE — a harmless way to wake the database from outside
-- ============================================================================
-- Supabase pauses a free-plan project after about a week without database
-- activity, and a paused project only comes back with a click in its
-- dashboard. Any real query resets that clock. This function is the smallest
-- one there is, and anything that pings on a schedule (Mosayic's keep-alive,
-- a GitHub Actions cron, an uptime monitor) can call it with nothing but the
-- project's public key:
--
--   GET https://<project-ref>.supabase.co/rest/v1/rpc/keepalive
--   apikey: <your publishable key>
--
-- It answers the database's current time. The fresh timestamp shows a live
-- database answered, not a cache. Why it's safe to leave open to anonymous
-- callers:
--
--   * It reads no table and takes no arguments. The only thing a caller learns
--     is that the database is awake.
--   * SECURITY INVOKER (the default): it runs as the caller, `anon`, so it
--     can reach nothing `anon` couldn't already reach.
--   * STABLE, so PostgREST serves it on a plain GET, inside a read-only
--     transaction.
--   * `search_path = ''`: nothing can be planted in the path for it to find.
--
-- Unlike an API route, this needs no server of your own. It exists in
-- production as soon as your first release runs the migrations.

CREATE OR REPLACE FUNCTION public.keepalive()
RETURNS timestamptz
LANGUAGE sql
STABLE
SET search_path = ''
AS $function$
    SELECT pg_catalog.now();
$function$;

REVOKE ALL ON FUNCTION public.keepalive() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.keepalive() TO anon, authenticated;
