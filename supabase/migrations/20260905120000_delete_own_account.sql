-- ============================================================================
-- ACCOUNT DELETION — from inside the app, with no server of your own
-- ============================================================================
-- Apple and Google require an in-app way to delete an account. Deleting a
-- user means deleting their row in auth.users, and no app user may touch that
-- table (try it: `set role authenticated; delete from auth.users;` →
-- permission denied). So the app calls this function instead —
-- `supabase.rpc('delete_own_account')` — and the function does the one thing
-- it is allowed to do. Why it is safe:
--
--   * SECURITY DEFINER: it runs with the privileges of its owner (the
--     `postgres` role that applies these migrations), not the caller's. That
--     is what lets it reach auth.users at all.
--   * It takes no arguments and only ever deletes auth.uid() — the user id
--     inside the caller's own session token. There is no way to name anyone
--     else.
--   * Only signed-in users may run it: EXECUTE is revoked from everyone and
--     granted to `authenticated`. An anonymous call is refused before the
--     body runs, and the body refuses again if there is somehow no uid.
--   * `search_path = ''` is the standard hardening for SECURITY DEFINER
--     functions: everything inside is schema-qualified, so nobody can plant
--     a look-alike object earlier in the search path.
--
-- Deleting the auth.users row cascades through Supabase's own auth tables
-- (identities, sessions, refresh tokens, MFA factors), and the
-- on_auth_user_deleted trigger from the initial schema removes the
-- public.users row, which cascades to devices. A session token issued before
-- the deletion stays syntactically valid until it expires (an hour at most),
-- but every table the user owned rows in is already empty, and Auth refuses
-- it. Files the user uploaded to Storage are NOT removed — add that here if
-- your app stores any.

CREATE OR REPLACE FUNCTION public.delete_own_account()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
    IF auth.uid() IS NULL THEN
        RAISE EXCEPTION 'delete_own_account: not signed in' USING ERRCODE = '42501';
    END IF;
    DELETE FROM auth.users WHERE id = auth.uid();
END;
$function$;

REVOKE ALL ON FUNCTION public.delete_own_account() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.delete_own_account() TO authenticated;
