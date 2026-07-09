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

st.set_page_config(page_title="Upload Data", page_icon="📂", layout="wide")
st.title("📂 Upload và Xử lý dữ liệu lớn")

uploaded_file = st.file_uploader("Chọn file dữ liệu bán hàng (Online Retail)", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success("Đọc dữ liệu thành công!")
    col_inf1, col_inf2 = st.columns(2)
    with col_inf1:
        st.metric("Số dòng thô nhận vào", f"{len(df):,}")
    with col_inf2:
        st.metric("Số cột", f"{len(df.columns)}")

    if st.button("🚀 Bắt đầu phân tích & Đồng bộ Cloud"):
        progress = st.progress(0)
        status = st.empty()  # Định nghĩa biến status chính xác tại đây

        # ==========================================
        # 1. XỬ LÝ DỮ LIỆU THÔ (Chạy ngầm)
        # ==========================================
        status.info("Đang làm sạch dữ liệu giao dịch...")
        df = clean_data(df)
        progress.progress(25)

        status.info("Đang tính toán các chỉ số định lượng RFM...")
        rfm = create_rfm(df)
        progress.progress(50)

        status.info("Đang phân cụm khách hàng bằng thuật toán K-Means...")
        rfm = segment_customer(rfm)
        rfm = rename_segment(rfm)
        progress.progress(75)

        status.info("Đang khai phá luật kết hợp bằng thuật toán Apriori...")
        df_apriori = df.head(50000) 
        rules = recommendation(df_apriori)
        progress.progress(90)

        # ==========================================
        # 2. ĐỒNG BỘ BẢNG SEGMENTS (XÓA CỦ - CHÈN MỚI)
        # ==========================================
        status.info("Đang làm sạch bảng phân khúc cũ trên Supabase...")
        try:
            supabase.table("segments").delete().neq("CustomerID", 0).execute()
        except:
            pass
        
        status.info("Đang đồng bộ kết quả phân khúc mới lên Supabase...")
        rfm_upload = rfm[["CustomerID", "Recency", "Frequency", "Monetary", "Cluster", "Segment"]].copy()
        rfm_upload["CustomerID"] = rfm_upload["CustomerID"].astype(int)
        rfm_upload["Cluster"] = rfm_upload["Cluster"].astype(int)
        rfm_upload["Recency"] = rfm_upload["Recency"].astype(float)
        rfm_upload["Frequency"] = rfm_upload["Frequency"].astype(float)
        rfm_upload["Monetary"] = rfm_upload["Monetary"].astype(float)
        
        segment_data = rfm_upload.to_dict("records")
        batch_size = 500 
        for i in range(0, len(segment_data), batch_size):
            batch = segment_data[i:i+batch_size]
            supabase.table("segments").insert(batch).execute()

        # ==========================================
        # 3. ĐỒNG BỘ BẢNG RECOMMENDATIONS (XÓA CŨ - CHÈN MỚI)
        # ==========================================
        status.info("Đang cập nhật tập luật gợi ý sản phẩm mới...")
        try:
            supabase.table("recommendations").delete().neq("id", 0).execute()
        except:
            pass

        rules_upload = rules[["antecedents", "consequents", "support", "confidence", "lift"]].copy()
        rules_upload["support"] = rules_upload["support"].astype(float)
        rules_upload["confidence"] = rules_upload["confidence"].astype(float)
        rules_upload["lift"] = rules_upload["lift"].astype(float)

        recommendation_data = rules_upload.head(100).to_dict("records")
        for i in range(0, len(recommendation_data), batch_size):
            batch = recommendation_data[i:i+batch_size]
            supabase.table("recommendations").insert(batch).execute()

        progress.progress(100)
        status.success(f"Hoàn thành! Đã tối ưu và lưu trữ thông tin lên Supabase.")
        st.balloons()

        # ==========================================
        # 4. HIỂN THỊ KẾT QUẢ & NÚT TẢI CHO POWER BI
        # ==========================================
        st.divider()
        st.subheader("📥 Xuất dữ liệu tích hợp cho Power BI")
        csv = rfm.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Tải file kết quả phân khúc khách hàng (CSV)",
            data=csv,
            file_name='customer_segments_results.csv',
            mime='text/csv',
        )

        st.divider()
        st.subheader("📊 Xem trước kết quả phân khúc khách hàng")
        st.dataframe(rfm.head(10))

        st.subheader("🛒 Xem trước các luật kết hợp sản phẩm")
        st.dataframe(rules.head(10))
