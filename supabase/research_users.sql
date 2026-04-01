create table if not exists public.research_users (
    id uuid primary key default gen_random_uuid(),
    username text unique not null,
    password text not null,
    display_name text,
    created_at timestamptz default now()
);

alter table public.research_users enable row level security;

-- service_role key bypasses RLS, so no policy needed for server access
