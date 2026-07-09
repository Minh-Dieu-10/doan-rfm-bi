import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import supabase

st.set_page_config(page_title="Khách hàng", page_icon="👤", layout="wide")
st.title("👤 Phân tích phân khúc khách hàng")

# Tải dữ liệu từ Supabase
try:
    response = supabase.table("segments").select("*").execute()
    data = response.data
    
    if not data:
        st.warning("Chưa có dữ liệu phân khúc. Vui lòng vào trang Upload Data để xử lý trước!")
    else:
        df_rfm = pd.DataFrame(data)
        
        # --- KHU VỰC THỐNG KÊ TỔNG QUAN ---
        st.subheader("📊 Chỉ số tổng quan")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Tổng khách hàng", f"{df_rfm['CustomerID'].nunique():,}")
        with col2:
            st.metric("Recency trung bình", f"{df_rfm['Recency'].mean():.1f} ngày")
        with col3:
            st.metric("Frequency trung bình", f"{df_rfm['Frequency'].mean():.1f} lần")
        with col4:
            st.metric("Monetary trung bình", f"${df_rfm['Monetary'].mean():,.2f}")
            
        st.divider()
        
        # --- ĐỒ THỊ TRỰC QUAN ---
        st.subheader("📈 Phân bố các phân khúc")
        
        # Đếm số lượng theo Segment
        segment_counts = df_rfm["Segment"].value_counts().reset_index()
        segment_counts.columns = ["Segment", "Count"]
        
        fig_pie = px.pie(segment_counts, values="Count", names="Segment", title="Tỷ lệ các nhóm khách hàng")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Biểu đồ Scatter 3D hoặc 2D xem phân cụm
        st.subheader("🎯 Ma trận phân cụm (Frequency vs Monetary)")
        fig_scatter = px.scatter(
            df_rfm, 
            x="Frequency", 
            y="Monetary", 
            color="Segment",
            log_x=True, 
            log_y=True,
            hover_data=["CustomerID", "Recency"],
            title="Biểu đồ phân cụm khách hàng (Log Scale)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # --- BẢNG TRA CỨU CHI TIẾT ---
        st.divider()
        st.subheader("🔍 Danh sách khách hàng chi tiết")
        
        # Bộ lọc theo phân khúc
        segments_list = ["Tất cả"] + df_rfm["Segment"].unique().tolist()
        selected_segment = st.selectbox("Chọn phân khúc để lọc:", segments_list)
        
        if selected_segment != "Tất cả":
            filtered_df = df_rfm[df_rfm["Segment"] == selected_segment]
        else:
            filtered_df = df_rfm
            
        st.dataframe(filtered_df[["CustomerID", "Recency", "Frequency", "Monetary", "Segment"]].reset_index(drop=True))

except Exception as e:
    st.error(f"Lỗi khi kết nối hoặc tải dữ liệu từ Supabase: {e}")
