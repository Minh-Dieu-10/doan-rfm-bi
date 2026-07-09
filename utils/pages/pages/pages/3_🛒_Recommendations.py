import streamlit as st
import pandas as pd
from utils.db import supabase

st.title("🛒 Đề xuất sản phẩm")

customer=st.text_input(
    "CustomerID"
)

if customer:

    data=supabase.table(
        "recommendations"
    ).select("*").eq(
        "customerid",
        customer
    ).execute()

    df=pd.DataFrame(data.data)

    st.dataframe(df)
