-- Create tables in public schema

-- 1. Users table (synchronized with auth.users)
create table if not exists public.users (
  id uuid references auth.users not null primary key,
  email text,
  full_name text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on users
alter table public.users enable row level security;

-- 2. Uploaded Images table
create table if not exists public.uploaded_images (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade not null,
  image_url text not null,
  annotated_image_url text,
  original_filename text not null,
  uploaded_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on uploaded_images
alter table public.uploaded_images enable row level security;

-- 3. Detections table
create table if not exists public.detections (
  id uuid default gen_random_uuid() primary key,
  image_id uuid references public.uploaded_images(id) on delete cascade not null,
  object_name text not null,
  confidence double precision not null,
  x_min double precision not null,
  y_min double precision not null,
  x_max double precision not null,
  y_max double precision not null,
  prompt_used text,
  processing_time double precision not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on detections
alter table public.detections enable row level security;

-- 4. Analytics table
create table if not exists public.analytics (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade not null unique,
  total_images integer default 0 not null,
  total_detections integer default 0 not null,
  most_detected_object text,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on analytics
alter table public.analytics enable row level security;

-- --- TRIGGERS AND FUNCTIONS ---

-- Trigger to copy user to public.users on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', '')
  );
  return new;
end;
$$ language plpgsql security definer;

-- Drop trigger if exists and recreate
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();


-- Recalculate analytics for a user
create or replace function public.recalculate_analytics(user_uuid uuid)
returns void as $$
declare
  t_images integer;
  t_detections integer;
  m_object text;
begin
  -- 1. Count images uploaded by user
  select count(*) into t_images 
  from public.uploaded_images 
  where user_id = user_uuid;
  
  -- 2. Count detections for the user
  select count(*) into t_detections 
  from public.detections d
  join public.uploaded_images i on d.image_id = i.id
  where i.user_id = user_uuid;
  
  -- 3. Get the most frequently detected object
  select object_name into m_object
  from (
    select d.object_name, count(*) as cnt
    from public.detections d
    join public.uploaded_images i on d.image_id = i.id
    where i.user_id = user_uuid
    group by d.object_name
    order by cnt desc, d.object_name asc
    limit 1
  ) sub;

  -- 4. Upsert analytics table
  insert into public.analytics (user_id, total_images, total_detections, most_detected_object, updated_at)
  values (user_uuid, t_images, t_detections, m_object, now())
  on conflict (user_id) do update
  set total_images = excluded.total_images,
      total_detections = excluded.total_detections,
      most_detected_object = excluded.most_detected_object,
      updated_at = now();
end;
$$ language plpgsql security definer;


-- Trigger functions to automatically update analytics on image/detection changes
create or replace function public.on_image_change()
returns trigger as $$
declare
  user_uuid uuid;
begin
  if tg_op = 'DELETE' then
    user_uuid := old.user_id;
  else
    user_uuid := new.user_id;
  end if;
  
  perform public.recalculate_analytics(user_uuid);
  return null;
end;
$$ language plpgsql security definer;

create or replace function public.on_detection_change()
returns trigger as $$
declare
  user_uuid uuid;
  img_id uuid;
begin
  if tg_op = 'DELETE' then
    img_id := old.image_id;
  else
    img_id := new.image_id;
  end if;

  select user_id into user_uuid 
  from public.uploaded_images 
  where id = img_id;

  if user_uuid is not null then
    perform public.recalculate_analytics(user_uuid);
  end if;
  
  return null;
end;
$$ language plpgsql security definer;

-- Attach Triggers to uploaded_images
drop trigger if exists image_changes_trigger on public.uploaded_images;
create trigger image_changes_trigger
  after insert or delete or update on public.uploaded_images
  for each row execute procedure public.on_image_change();

-- Attach Triggers to detections
drop trigger if exists detection_changes_trigger on public.detections;
create trigger detection_changes_trigger
  after insert or delete or update on public.detections
  for each row execute procedure public.on_detection_change();
