-- Add property_code and source_email_date to bills table
alter table bills
  add column if not exists property_code    text,
  add column if not exists source_email_date timestamptz;
