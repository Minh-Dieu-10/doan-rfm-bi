import streamlit as st
import pandas as pd
from utils.db import supabase

st.title("👥 Danh sách khách hàng")

data=supabase.table(
    "Dim_Customer"
).select("*").execute()

df=pd.DataFrame(data.data)

st.dataframe(df)

customer=st.text_input(
    "Nhập CustomerID"
)

if customer:

    result=df[
        df["customerid"]==customer
    ]

    st.write(result)
