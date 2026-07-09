import streamlit as st
import pandas as pd

from utils.processing import (
    clean_data,
    create_rfm,
    segment_customer,
    rename_segment,
    recommendation
)

from utils.db import supabase


st.set_page_config(page_title="Upload Data", page_icon="📂")

st.title("📂 Upload và Phân tích dữ liệu")

st.markdown("""
Upload dữ liệu bán hàng để:

- Làm sạch dữ liệu
- Phân tích RFM
- Phân khúc khách hàng bằng K-Means
- Phân tích giỏ hàng bằng Apriori
- Lưu kết quả lên Supabase
""")

uploaded_file = st.file_uploader(
    "Chọn file dữ liệu",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:

    # ==========================
    # ĐỌC FILE
    # ==========================

    if uploaded_file.name.endswith(".csv"):

        df = pd.read_csv(uploaded_file)

    else:

        df = pd.read_excel(uploaded_file)

    st.success("Đọc dữ liệu thành công!")

    st.write("### Xem trước dữ liệu")

    st.dataframe(df.head())

    st.write(f"Số dòng: {len(df)}")

    st.write(f"Số cột: {len(df.columns)}")


    # ==========================
    # NÚT XỬ LÝ
    # ==========================

    if st.button("🚀 Bắt đầu xử lý"):

        progress = st.progress(0)

        status = st.empty()


        # ==========================
        # CLEAN DATA
        # ==========================

        status.info("Đang làm sạch dữ liệu...")

        df = clean_data(df)

        progress.progress(20)


        # ==========================
        # RFM
        # ==========================

        status.info("Đang phân tích RFM...")

        rfm = create_rfm(df)

        progress.progress(40)


        # ==========================
        # KMEANS
        # ==========================

        status.info("Đang phân cụm khách hàng...")

        rfm = segment_customer(rfm)

        rfm = rename_segment(rfm)

        progress.progress(60)


        # ==========================
        # APRIORI
        # ==========================

        status.info("Đang phân tích giỏ hàng...")

        rules = recommendation(df)

        progress.progress(80)


        # ==========================
        # UPLOAD SEGMENTS
        # ==========================

        status.info("Đang upload Segment...")

        try:

            supabase.table("segments").delete().neq(
                "CustomerID",
                0
            ).execute()

        except:
            pass

        segment_data = rfm.to_dict("records")

        batch_size = 500

        for i in range(0, len(segment_data), batch_size):

            batch = segment_data[i:i+batch_size]

            supabase.table("segments").insert(batch).execute()


        # ==========================
        # UPLOAD RECOMMENDATION
        # ==========================

        status.info("Đang upload Recommendation...")

        try:

            supabase.table("recommendations").delete().neq(
                "id",
                0
            ).execute()

        except:
            pass

        recommendation_data = rules.to_dict("records")

        for i in range(0, len(recommendation_data), batch_size):

            batch = recommendation_data[i:i+batch_size]

            supabase.table("recommendations").insert(batch).execute()


        progress.progress(100)

        status.success("Hoàn thành!")

        st.balloons()

        # ==========================
        # HIỂN THỊ KẾT QUẢ
        # ==========================

        st.divider()

        st.subheader("📊 Phân khúc khách hàng")

        st.dataframe(rfm.head(20))

        st.divider()

        st.subheader("🛒 Luật kết hợp")

        st.dataframe(rules.head(20))
