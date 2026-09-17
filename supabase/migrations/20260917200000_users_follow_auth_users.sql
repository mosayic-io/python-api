-- ============================================================================
-- A PROFILE ROW BELONGS TO ITS ACCOUNT — SAID WITH A FOREIGN KEY
-- ============================================================================
-- `public.users.id` IS the `auth.users` id, so the row is a child of the
-- account and should go when the account goes. Until now a trigger
-- (`on_auth_user_deleted`) deleted it by hand. A foreign key says the same
-- thing to the database itself, which is better in three ways:
--
--   * It cannot be forgotten. The trigger only ran for DELETE statements
--     against auth.users; the key is enforced by the database.
--   * It rules out the other orphan too: a profile row can no longer be
--     inserted for an account that does not exist.
--   * It is one mechanism instead of two, so nothing can half-happen.
--
-- Deleting an account still cascades on to `devices` (and any other table
-- whose foreign key points at public.users), exactly as before.

-- Any profile row whose account is already gone would refuse the key. There
-- should be none — the trigger removed them — but a database that was
-- restored, or written to by hand, may have one. They belong to no account
-- and nothing can reach them, so they go.
DELETE FROM public.users u
WHERE NOT EXISTS (SELECT 1 FROM auth.users a WHERE a.id = u.id);

ALTER TABLE public.users
    ADD CONSTRAINT users_auth_user_fkey
    FOREIGN KEY (id)
    REFERENCES auth.users(id)
    ON DELETE CASCADE;

-- The trigger and its function have nothing left to do.
DROP TRIGGER IF EXISTS on_auth_user_deleted ON auth.users;
DROP FUNCTION IF EXISTS public.handle_deleted_user();
