-- Enable RLS on all tables (already run in schema.sql, repeating for completeness)
alter table public.users enable row level security;
alter table public.uploaded_images enable row level security;
alter table public.detections enable row level security;
alter table public.analytics enable row level security;

-- 1. Users policies
create policy "Users can view their own profile"
on public.users for select
using (auth.uid() = id);

create policy "Users can update their own profile"
on public.users for update
using (auth.uid() = id);

-- 2. Uploaded Images policies
create policy "Users can view their own uploaded images"
on public.uploaded_images for select
using (auth.uid() = user_id);

create policy "Users can insert their own uploaded images"
on public.uploaded_images for insert
with check (auth.uid() = user_id);

create policy "Users can update their own uploaded images"
on public.uploaded_images for update
using (auth.uid() = user_id);

create policy "Users can delete their own uploaded images"
on public.uploaded_images for delete
using (auth.uid() = user_id);

-- 3. Detections policies
create policy "Users can view detections of their own images"
on public.detections for select
using (
  exists (
    select 1 
    from public.uploaded_images 
    where public.uploaded_images.id = public.detections.image_id 
      and public.uploaded_images.user_id = auth.uid()
  )
);

create policy "Users can insert detections for their own images"
on public.detections for insert
with check (
  exists (
    select 1 
    from public.uploaded_images 
    where public.uploaded_images.id = image_id 
      and public.uploaded_images.user_id = auth.uid()
  )
);

create policy "Users can delete detections of their own images"
on public.detections for delete
using (
  exists (
    select 1 
    from public.uploaded_images 
    where public.uploaded_images.id = public.detections.image_id 
      and public.uploaded_images.user_id = auth.uid()
  )
);

-- 4. Analytics policies
create policy "Users can view their own analytics"
on public.analytics for select
using (auth.uid() = user_id);
