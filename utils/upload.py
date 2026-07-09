from utils.db import supabase

def upload_segments(df):

    supabase.table("segments").delete().neq("CustomerID",0).execute()

    data=df.to_dict("records")

    supabase.table("segments").insert(data).execute()


def upload_recommend(df):

    supabase.table("recommendations").delete().neq("id",0).execute()

    data=df.to_dict("records")

    supabase.table("recommendations").insert(data).execute()
