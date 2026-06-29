-- ============================================================================
-- Silkhaus Finance Hub — Initial Schema
-- Run once in Supabase SQL Editor (paste & Run).
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. Roles
-- ---------------------------------------------------------------------------
create type app_role as enum ('admin', 'preparer', 'approver', 'viewer');

-- ---------------------------------------------------------------------------
-- 2. Profiles — one row per user, extends auth.users with their app role
-- ---------------------------------------------------------------------------
create table profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  email       text not null,
  full_name   text,
  avatar_url  text,
  role        app_role not null default 'viewer',
  created_at  timestamptz not null default now()
);

-- Auto-create profile row on Google Sign-In (role defaults to viewer;
-- admin promotes them from the admin panel)
create function handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, full_name, avatar_url)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'full_name',
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure handle_new_user();

-- ---------------------------------------------------------------------------
-- 3. Bills — one row per invoice processed
-- ---------------------------------------------------------------------------
create type bill_status as enum ('pending_review', 'approved', 'rejected', 'exported');

create table bills (
  id                        uuid primary key default gen_random_uuid(),

  -- Core bill fields (extracted by AI)
  vendor_name               text,
  bill_number               text,
  bill_date                 date,
  due_date                  date,
  currency                  text not null default 'AED',
  amount                    numeric(14,2),
  tax_amount                numeric(14,2),

  -- Classification
  category                  text,          -- e.g. "Utilities - Electricity"
  expense_nature            text default 'Opex',
  property_name             text,          -- which Silkhaus property this is for

  -- NetSuite export fields
  suggested_debit_account   text,          -- e.g. "Utilities Expense"
  suggested_credit_account  text default 'Accounts Payable',
  netsuite_memo             text,          -- generated memo for NetSuite line

  -- AI output (full)
  suggested_je              jsonb,         -- structured DR/CR lines
  extracted_data            jsonb,         -- raw Claude output (audit trail)
  confidence_notes          text,          -- anything Claude was unsure about

  -- Source tracking
  source                    text default 'manual_upload',  -- 'gmail_sync' | 'manual_upload'
  source_email_id           text,          -- Gmail message ID for deduplication
  source_email_subject      text,
  source_email_from         text,
  attachment_path           text,          -- path in Supabase Storage

  -- Review
  status                    bill_status not null default 'pending_review',
  reviewed_by               uuid references profiles(id),
  reviewed_at               timestamptz,
  review_notes              text,

  created_at                timestamptz not null default now(),
  updated_at                timestamptz not null default now()
);

create index bills_status_idx   on bills(status);
create index bills_vendor_idx   on bills(vendor_name);
create index bills_date_idx     on bills(bill_date);
create index bills_category_idx on bills(category);
create index bills_email_id_idx on bills(source_email_id);  -- deduplication

-- ---------------------------------------------------------------------------
-- 4. App settings (Gmail tokens, last sync time, etc.)
-- ---------------------------------------------------------------------------
create table settings (
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

create function current_role_name()
returns app_role as $$
  select role from profiles where id = auth.uid();
$$ language sql security definer stable;

-- profiles: see own row or admin sees all
create policy "profiles select" on profiles
  for select using (id = auth.uid() or current_role_name() = 'admin');
create policy "profiles update" on profiles
  for update using (current_role_name() = 'admin');

-- bills: all authenticated roles can read; preparer/admin can write
create policy "bills select" on bills
  for select using (current_role_name() in ('admin','preparer','approver','viewer'));
create policy "bills insert" on bills
  for insert with check (current_role_name() in ('admin','preparer'));
create policy "bills update" on bills
  for update using (current_role_name() in ('admin','preparer','approver'));

-- settings: admin only
create policy "settings all" on settings
  for all using (current_role_name() = 'admin');

-- ---------------------------------------------------------------------------
-- 6. Storage bucket for original invoice files
-- ---------------------------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('bill-attachments', 'bill-attachments', false)
on conflict (id) do nothing;

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
