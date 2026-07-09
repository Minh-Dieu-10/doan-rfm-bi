
from utils.db import supabase

def upload_table(df, table_name):

    data = df.to_dict("records")

    supabase.table(table_name).insert(data).execute()
