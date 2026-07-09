from supabase import create_client

SUPABASE_URL = "https://cylljidqxzublpipypcu.supabase.co"
SUPABASE_KEY = "sb_publishable_3DEP2QBBrM7uT0AZmj4Wpw_9fcnn8h6"

supabase=create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()
