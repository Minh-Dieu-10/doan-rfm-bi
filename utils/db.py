from supabase import create_client

SUPABASE_URL="YOUR_URL"
SUPABASE_KEY="YOUR_KEY"

supabase=create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
