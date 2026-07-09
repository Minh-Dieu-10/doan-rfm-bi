from supabase import create_client

SUPABASE_URL = "https://cylljidqxzublpipypcu.supabase.co"
SUPABASE_KEY = "sb_publishable_3DEP2QBBrM7uT0AZmj4Wpw_9fcnn8h6"

supabase=create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
