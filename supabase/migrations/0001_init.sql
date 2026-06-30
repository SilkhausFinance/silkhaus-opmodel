-- ============================================================================
-- Silkhaus Finance Hub — Initial Schema
-- Safe to re-run: all statements use IF NOT EXISTS / OR REPLACE / DO blocks.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Enums
-- ---------------------------------------------------------------------------
do $$ begin
  create type app_role as enum ('admin', 'preparer', 'approver', 'viewer');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type bill_status as enum ('pending_review', 'approved', 'rejected', 'exported');
exception when duplicate_object then null;
end $$;

-- ---------------------------------------------------------------------------
-- 2. Profiles — one row per user, extends auth.users with their app role
-- ---------------------------------------------------------------------------
create table if not exists profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text not null,
  full_name   text,
  avatar_url  text,
  role        app_role not null default 'viewer',
  created_at  timestamptz not null default now()
);

create or replace function handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name, avatar_url)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'avatar_url'
  )
  on conflict (id) do nothing;
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();

-- ---------------------------------------------------------------------------
-- 3. Bills — one row per invoice processed
-- ---------------------------------------------------------------------------
create table if not exists bills (
  id                        uuid primary key default gen_random_uuid(),

  vendor_name               text,
  bill_number               text,
  bill_date                 date,
  due_date                  date,
  currency                  text not null default 'AED',
  amount                    numeric(14,2),
  tax_amount                numeric(14,2),

  category                  text,
  expense_nature            text default 'Opex',
  property_name             text,

  suggested_debit_account   text,
  suggested_credit_account  text default 'Accounts Payable',
  netsuite_memo             text,

  suggested_je              jsonb,
  extracted_data            jsonb,
  confidence_notes          text,

  source                    text default 'manual_upload',
  source_email_id           text,
  source_email_subject      text,
  source_email_from         text,
  attachment_path           text,

  status                    bill_status not null default 'pending_review',
  reviewed_by               uuid references profiles(id),
  reviewed_at               timestamptz,
  review_notes              text,

  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);

create index if not exists bills_status_idx   on bills(status);
create index if not exists bills_vendor_idx   on bills(vendor_name);
create index if not exists bills_date_idx     on bills(bill_date);
create index if not exists bills_category_idx on bills(category);
create index if not exists bills_email_id_idx on bills(source_email_id);

-- ---------------------------------------------------------------------------
-- 4. Settings (Gmail tokens, last sync time, etc.)
-- ---------------------------------------------------------------------------
create table if not exists settings (
  key        text primary key,
  value      text not null,
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- 5. Row-Level Security
-- ---------------------------------------------------------------------------
alter table profiles  enable row level security;
alter table bills     enable row level security;
alter table settings  enable row level security;

create or replace function current_role_name()
returns app_role as $$
  select role from profiles where id = auth.uid();
$$ language sql security definer stable;

drop policy if exists "profiles select" on profiles;
drop policy if exists "profiles update" on profiles;
drop policy if exists "bills select"    on bills;
drop policy if exists "bills insert"    on bills;
drop policy if exists "bills update"    on bills;
drop policy if exists "settings all"    on settings;

create policy "profiles select" on profiles
  for select using (id = auth.uid() or current_role_name() = 'admin');
create policy "profiles update" on profiles
  for update using (current_role_name() = 'admin');

create policy "bills select" on bills
  for select using (current_role_name() in ('admin','preparer','approver','viewer'));
create policy "bills insert" on bills
  for insert with check (current_role_name() in ('admin','preparer'));
create policy "bills update" on bills
  for update using (current_role_name() in ('admin','preparer','approver'));

create policy "settings all" on settings
  for all using (current_role_name() = 'admin');

-- ---------------------------------------------------------------------------
-- 6. Storage bucket for original invoice files
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('bill-attachments', 'bill-attachments', false)
on conflict (id) do nothing;

drop policy if exists "attachments select" on storage.objects;
drop policy if exists "attachments insert" on storage.objects;

create policy "attachments select" on storage.objects
  for select using (
    bucket_id = 'bill-attachments'
    and current_role_name() in ('admin','preparer','approver')
  );
create policy "attachments insert" on storage.objects
  for insert with check (
    bucket_id = 'bill-attachments'
    and current_role_name() in ('admin','preparer')
  );
