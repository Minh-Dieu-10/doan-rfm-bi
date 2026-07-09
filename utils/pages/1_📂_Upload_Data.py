import streamlit as st

st.title("📂 Upload dữ liệu")

file=st.file_uploader(
    "Chọn file",
    type=["csv","xlsx"]
)

if file:

    st.success("Đã nhận file.")

    if st.button("Chạy ETL"):

        st.info("Cleaning...")

        st.info("RFM...")

        st.info("KMeans...")

        st.info("Apriori...")

        st.success("Đã lưu lên Supabase.")
