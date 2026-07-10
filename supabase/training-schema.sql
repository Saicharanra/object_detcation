-- Create training_jobs table in public schema
create table if not exists public.training_jobs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references public.users(id) on delete cascade not null,
  status text default 'pending' not null, -- 'pending', 'training', 'completed', 'failed'
  epochs integer default 5 not null,
  trained_classes text[], -- List of classes the model was trained on
  error_message text,
  completed_at timestamp with time zone,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.training_jobs enable row level security;

-- Create policies for training_jobs (Users can read and write their own training jobs)
create policy "Users can view their own training jobs" 
  on public.training_jobs for select 
  using (auth.uid() = user_id);

create policy "Users can insert their own training jobs" 
  on public.training_jobs for insert 
  with check (auth.uid() = user_id);

create policy "Users can update their own training jobs" 
  on public.training_jobs for update 
  using (auth.uid() = user_id);
