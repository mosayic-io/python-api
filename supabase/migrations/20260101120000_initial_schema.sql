-- ============================================================================
-- TABLES
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE public.users (
    id uuid NOT NULL,
    email text,
    display_name text,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    photo_url text
);

CREATE TABLE public.devices (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL,
    fcm_token text NOT NULL,
    created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PRIMARY KEYS
-- ============================================================================

CREATE UNIQUE INDEX users_pkey ON public.users USING btree (id);
ALTER TABLE public.users ADD CONSTRAINT users_pkey PRIMARY KEY USING INDEX users_pkey;

CREATE UNIQUE INDEX devices_pkey ON public.devices USING btree (id);
ALTER TABLE public.devices ADD CONSTRAINT devices_pkey PRIMARY KEY USING INDEX devices_pkey;

CREATE UNIQUE INDEX devices_user_id_fcm_token_key ON public.devices USING btree (user_id, fcm_token);
ALTER TABLE public.devices
    ADD CONSTRAINT devices_user_id_fcm_token_key
    UNIQUE USING INDEX devices_user_id_fcm_token_key;

CREATE INDEX devices_user_id_idx ON public.devices USING btree (user_id);

ALTER TABLE public.devices
    ADD CONSTRAINT devices_user_id_fkey
    FOREIGN KEY (user_id)
    REFERENCES public.users(id)
    ON DELETE CASCADE;

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.devices ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can view their own data"
    ON public.users
    AS PERMISSIVE
    FOR SELECT
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Users can update their data"
    ON public.users
    AS PERMISSIVE
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can delete their own data"
    ON public.users
    AS PERMISSIVE
    FOR DELETE
    TO authenticated
    USING (auth.uid() = id);

-- Devices table policies
CREATE POLICY "Users can view their own devices"
    ON public.devices
    AS PERMISSIVE
    FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own devices"
    ON public.devices
    AS PERMISSIVE
    FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own devices"
    ON public.devices
    AS PERMISSIVE
    FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own devices"
    ON public.devices
    AS PERMISSIVE
    FOR DELETE
    TO authenticated
    USING (auth.uid() = user_id);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

SET check_function_bodies = OFF;

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
BEGIN
    INSERT INTO public.users (id, display_name, email, photo_url)
    VALUES (
        NEW.id,
        NEW.raw_user_meta_data->>'full_name',
        NEW.email,
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$function$;

CREATE OR REPLACE FUNCTION public.handle_deleted_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
AS $function$
BEGIN
    DELETE FROM public.users WHERE id = OLD.id;
    RETURN OLD;
END;
$function$;

CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$function$;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

CREATE TRIGGER on_auth_user_deleted
    AFTER DELETE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_deleted_user();

CREATE TRIGGER on_users_updated
    BEFORE UPDATE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER on_devices_updated
    BEFORE UPDATE ON public.devices
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();
