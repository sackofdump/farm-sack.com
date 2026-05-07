-- =====================================================================
-- FarmSack Leaderboard table + RLS
-- Run this once in your Supabase SQL editor (Dashboard → SQL → New query).
-- =====================================================================

create table if not exists public.leaderboard (
  user_id              uuid primary key references auth.users (id) on delete cascade,
  farmer_name          text not null,
  level                int  not null default 1,
  coins                int  not null default 0,
  day_count            int  not null default 1,
  harvested            int  not null default 0,
  planted              int  not null default 0,
  plowed               int  not null default 0,
  watered              int  not null default 0,
  trees_placed         int  not null default 0,
  animals_owned        int  not null default 0,
  animals_slaughtered  int  not null default 0,
  daily_streak         int  not null default 0,
  quests_done          int  not null default 0,
  dailies_done         int  not null default 0,
  updated_at           timestamptz not null default now()
);

-- Migration for existing tables:
alter table public.leaderboard
  add column if not exists animals_owned       int not null default 0,
  add column if not exists animals_slaughtered int not null default 0,
  add column if not exists staff_harvested     int not null default 0,
  add column if not exists prestige_count      int not null default 0,
  add column if not exists prestige_bonus_pct  numeric(8,2) not null default 0;

-- Widen prestige_bonus_pct from int to numeric(8,2) on installs that
-- predate this change. Prestige bonus is now tracked to 0.01% precision
-- in-game (e.g. 46.55% from a reset at 46.55M coins), so the leaderboard
-- column has to accept fractional percent values too. Idempotent:
-- re-running against a column that's already numeric(8,2) is a no-op.
alter table public.leaderboard
  alter column prestige_bonus_pct type numeric(8,2)
  using prestige_bonus_pct::numeric(8,2);

-- Indexes for the two sort orders the leaderboard uses.
create index if not exists leaderboard_level_coins_idx
  on public.leaderboard (level desc, coins desc);
create index if not exists leaderboard_updated_idx
  on public.leaderboard (updated_at desc);

-- Row-level security: anyone can read; only owners can write their own row.
alter table public.leaderboard enable row level security;

drop policy if exists "leaderboard_select_all"  on public.leaderboard;
drop policy if exists "leaderboard_upsert_own"  on public.leaderboard;
drop policy if exists "leaderboard_update_own"  on public.leaderboard;
drop policy if exists "leaderboard_delete_own"  on public.leaderboard;

create policy "leaderboard_select_all"
  on public.leaderboard
  for select
  to anon, authenticated
  using (true);

create policy "leaderboard_upsert_own"
  on public.leaderboard
  for insert
  to authenticated
  with check (user_id = auth.uid());

create policy "leaderboard_update_own"
  on public.leaderboard
  for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "leaderboard_delete_own"
  on public.leaderboard
  for delete
  to authenticated
  using (user_id = auth.uid());
