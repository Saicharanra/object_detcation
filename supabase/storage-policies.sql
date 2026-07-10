-- 1. Create the bucket
insert into storage.buckets (id, name, public)
values ('object-detection', 'object-detection', true)
on conflict (id) do nothing;

-- 2. Enable row level security on storage.objects if not already done (done by default in Supabase)

-- 3. Define Policies for the 'object-detection' bucket

-- Policy for viewing/downloading files: public access is allowed
create policy "Allow public read access"
on storage.objects for select
using (bucket_id = 'object-detection');

-- Policy for uploading files: only authenticated users can upload, and only into their own subfolder
create policy "Allow authenticated uploads to user folder"
on storage.objects for insert
to authenticated
with check (
  bucket_id = 'object-detection' 
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy for deleting files: only the authenticated owner of the folder can delete files
create policy "Allow authenticated delete of own files"
on storage.objects for delete
to authenticated
using (
  bucket_id = 'object-detection' 
  and (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy for updating files: only the authenticated owner of the folder can update files
create policy "Allow authenticated update of own files"
on storage.objects for update
to authenticated
using (
  bucket_id = 'object-detection' 
  and (storage.foldername(name))[1] = auth.uid()::text
);
