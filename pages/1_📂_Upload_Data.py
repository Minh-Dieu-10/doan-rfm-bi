import streamlit as st
import pandas as pd

from utils.cleaning import clean_data
from utils.rfm import create_rfm
from utils.kmeans import segment_customer
from utils.apriori import recommendation
from utils.upload import upload_table

st.title("📂 Upload dữ liệu")

file = st.file_uploader(
    "Chọn file Excel",
    type=["xlsx","csv"]
)

if file:

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    st.success("Đọc dữ liệu thành công!")

    if st.button("🚀 Xử lý dữ liệu"):

        df = clean_data(df)

        rfm = create_rfm(df)

        segment = segment_customer(rfm)

        recommend = recommendation(df)

        upload_table(segment,"segments")

        upload_table(recommend,"recommendations")

        st.success("Hoàn tất!")
