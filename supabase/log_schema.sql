create extension if not exists pgcrypto;

create table if not exists public.sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.research_users(id) on delete set null,
    scenario text,
    start_time timestamptz,
    end_time timestamptz,
    result text,
    total_turns int4,
    final_orientation int4,
    final_anxiety int4,
    final_aggression int4
);

create table if not exists public.interactions (
    id uuid primary key default gen_random_uuid(),
    session_id uuid references public.sessions(id) on delete cascade,
    turn int4,
    nurse_input text,
    patient_response text,
    analysis jsonb,
    patient_state jsonb,
    nurse_state jsonb,
    phase int4,
    username text,
    created_at timestamptz
);

create index if not exists idx_sessions_scenario
    on public.sessions (scenario);

create index if not exists idx_sessions_start_time
    on public.sessions (start_time desc);

create index if not exists idx_interactions_session_turn
    on public.interactions (session_id, turn);

create index if not exists idx_interactions_created_at
    on public.interactions (created_at desc);
