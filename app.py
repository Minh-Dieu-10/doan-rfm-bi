import streamlit as st
import pandas as pd
from supabase import create_client, Client

#--- THÔNG TIN KẾT NỐI API SUPABASE ---
SUPABASE_URL = "https://cylljidqxzublpipypcu.supabase.co"
SUPABASE_KEY = "sb_publishable_3DEP2QBBrM7uT0AZmj4Wpw_9fcnn8h6"

#Khởi tạo kết nối qua API
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Lỗi khởi tạo Supabase Client: {e}")

#--- CHƯƠNG TRÌNH CHÍNH (STREAMLIT APP) ---
st.set_page_config(page_title="Hệ thống Phân tích RFM", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔑 ĐĂNG NHẬP HỆ THỐNG")
    username = st.text_input("Tài khoản admin")
    password = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if username == "admin" and password == "123456":
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu!")
else:
    st.title("🚀 HỆ THỐNG XỬ LÝ DỮ LIỆU & PHÂN TÍCH RFM KHÁCH HÀNG")
    st.sidebar.button("Đăng xuất", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    st.subheader("📁 Bước 1: Nạp file dữ liệu bán hàng")
    uploaded_file = st.file_uploader("Chọn file OnlineRetail (.csv hoặc .xlsx)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
            else:
                df = pd.read_excel(uploaded_file)
                
            st.success(f"Đã tải file thành công! Số lượng bản ghi: {len(df):,}")
            st.dataframe(df.head(5))
            
            # --- 1. KHỞI TẠO BỘ NHỚ TẠM (SESSION STATE) ---
            if "etl_success" not in st.session_state:
                st.session_state.etl_success = False
            if "rfm_data" not in st.session_state:
                st.session_state.rfm_data = None

            st.subheader("⚙️ Bước 2: Kích hoạt quy trình xử lý dữ liệu (ETL)")
            
            # --- 2. NÚT BẤM KÍCH HOẠT QUY TRÌNH ETL ---
            if st.button("Kích hoạt quy trình ETL"):
                try:
                    with st.spinner("Đang làm sạch dữ liệu, tính toán RFM và đẩy vào Supabase qua API..."):
                        # Làm sạch dữ liệu
                        df = df.dropna(subset=['CustomerID'])
                        df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
                        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
                        df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
                        df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]

                        df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
                        df = df.dropna(subset=['InvoiceDate'])
                        df['TotalAmount'] = df['Quantity'] * df['UnitPrice']

                        # --- ĐOẠN CODE TÍNH TOÁN RFM ---
                     
                        # Tính ngày hiện tại làm mốc (Ngày mua cuối cùng toàn hệ thống + 1)
                        snapshot_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
                        
                        # Gom nhóm theo từng khách hàng
                        rfm = df.groupby('CustomerID').agg({
                            'InvoiceDate': lambda x: (snapshot_date - x.max()).days,
                            'InvoiceNo': 'nunique',
                            'TotalAmount': 'sum'
                        }).reset_index()
                        
                        rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
                        
                        # Chia điểm từ 1-5 bằng qcut
                        rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1], duplicates='drop')
                        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
                        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
                        
                        # Tính chuỗi RFM_Score
                        rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
                        
                        # Định nghĩa hàm phân nhóm Marketing
                        def segment_rfm(row):
                            r = int(row['R_Score'])
                            f = int(row['F_Score'])
                            m = int(row['M_Score'])
                            if r >= 4 and f >= 4 and m >= 4:
                                return "Champions (Khách hàng VIP)"
                            elif r >= 3 and f >= 3:
                                return "Loyal Customers (Khách hàng thân thiết)"
                            elif r <= 2 and f >= 3:
                                return "At Risk (Khách hàng có nguy cơ rời bỏ)"
                            else:
                                return "Normal Customers (Khách hàng phổ thông)"
                                
                        rfm['rfm_group'] = rfm.apply(segment_rfm, axis=1)

                        # --- GỬI DỮ LIỆU LÊN SUPABASE ---
                        # Chỉ lọc lấy đúng các cột có tồn tại trên database Supabase 
                        columns_to_db = ['CustomerID', 'Recency', 'Frequency', 'Monetary', 'RFM_Score', 'rfm_group']
                        rfm_filtered = rfm[columns_to_db]
                        # Đổi tên cột sang viết thường hoàn toàn để khớp 100% với database Supabase
                        rfm_to_send = rfm.rename(columns={
                            'CustomerID': 'customerid', 
                            'Recency': 'recency',
                            'Frequency': 'frequency',
                            'Monetary': 'monetary',
                            'RFM_Score': 'rfm_score',
                            'rfm_group': 'rfm_group'
                        })
                        # Chuyển DataFrame thành list json để đẩy qua API
                        records = rfm_to_send.to_dict(orient="records")
                        batch_size = 1000
                        for i in range(0, len(records), batch_size):
                            batch = records[i:i+batch_size]
                            supabase.table("Dim_Customer").upsert(batch).execute()

                        # LƯU KẾT QUẢ VÀO BỘ NHỚ TẠM SAU KHI THÀNH CÔNG
                        st.session_state.etl_success = True
                        st.session_state.rfm_data = rfm
                        
                        st.success("🎉 Quy trình ETL hoàn tất!")
                        st.balloons()

                except Exception as ex:
                    st.error(f"Có lỗi xảy ra khi xử lý file hoặc đẩy API: {ex}")

            # --- 3. KHỐI HIỂN THỊ ĐỘC LẬP (GIỮ NGUYÊN GIAO DIỆN KHI DOWNLOAD FILE) ---
            if st.session_state.etl_success and st.session_state.rfm_data is not None:
                # Lấy dữ liệu từ bộ nhớ tạm ra để hiển thị
                rfm_cached = st.session_state.rfm_data
                
                st.write("📊 Kết quả phân tích phân khúc khách hàng:")
                st.dataframe(rfm_cached.head(10))
                
                # --- KHỐI LỆNH NÚT DOWNLOAD ---
                st.subheader("📥 Xuất báo cáo phân khúc khách hàng")

                # Tạo file CSV
                csv_data = rfm_cached.to_csv(index=False).encode('utf-8-sig')

                # Tạo file Excel bằng BytesIO
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    rfm_cached.to_excel(writer, index=False, sheet_name='RFM Segment')
                excel_data = buffer.getvalue()

                # Hiển thị 2 nút bấm tải file trên 2 cột
                col_down1, col_down2 = st.columns(2)
                with col_down1:
                    st.download_button(
                        label="🟢 Tải báo cáo (.xlsx)",
                        data=excel_data,
                        file_name="Bao_cao_phan_khuc_RFM.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                with col_down2:
                    st.download_button(
                        label="🔵 Tải dữ liệu (.csv)",
                        data=csv_data,
                        file_name="Du_lieu_phan_khuc_RFM.csv",
                        mime="text/csv"
                    )

                # --- KHỐI LỆNH DASHBOARD MARKETING ---
                st.markdown("---")
                st.header("📊 Dashboard Marketing & Gợi ý Chiến lược RFM")

                # Tính toán số liệu phân khúc
                segment_counts = rfm_cached['rfm_group'].value_counts().reset_index()
                segment_counts.columns = ['Phân khúc', 'Số lượng']
                segment_counts['Tỷ lệ (%)'] = (segment_counts['Số lượng'] / segment_counts['Số lượng'].sum() * 100).round(2)

                st.subheader("📈 Thống kê các phân khúc khách hàng")
                st.dataframe(segment_counts)
                st.bar_chart(data=segment_counts, x='Phân khúc', y='Số lượng', use_container_width=True)

                st.subheader("💡 Gợi ý chiến lược hành động Marketing")
                list_segments = segment_counts['Phân khúc'].tolist()
                if list_segments:
                    tabs = st.tabs(list_segments)
                    for idx, seg_name in enumerate(list_segments):
                        with tabs[idx]:
                            st.write(f"### Chiến lược dành cho nhóm **{seg_name}**")
                            if "Champions" in seg_name:
                                st.success("🎯 **Mục tiêu:** Giữ chân và biến họ thành đại sứ thương hiệu.")
                                st.markdown("""
                                * **Hành động:** Áp dụng chương trình tri ân đặc quyền (VIP Club), tặng quà sinh nhật cao cấp, trải nghiệm sớm bộ sưu tập mới.
                                * **Ưu đãi:** Tập trung vào cá nhân hóa trải nghiệm và dịch vụ chăm sóc khách hàng VIP.
                                """)
                            elif "Loyal" in seg_name or "Thân thiết" in seg_name:
                                st.info("⭐ **Mục tiêu:** Gia tăng giá trị đơn hàng (Upsell).")
                                st.markdown("""
                                * **Hành động:** Gợi ý các dòng sản phẩm phân khúc cao hơn, giới thiệu chương trình tích điểm đổi quà độc quyền.
                                * **Ưu đãi:** Tặng voucher mua hàng cho các đơn hàng đạt giá trị tối thiểu tiếp theo.
                                """)
                            elif "At Risk" in seg_name or "Nguy cơ" in seg_name:
                                st.warning("⚠️ **Mục tiêu:** Cứu vãn và kích hoạt lại (Re-engage).")
                                thong_diep = "Chúng tôi nhớ bạn"
                                st.markdown(f"""
                                * **Hành động:** Gửi thông điệp hỏi thăm cá nhân hóa thông qua SMS/Email với nội dung '{thong_diep}', tạo các chương trình khảo sát nhận quà để tìm hiểu nguyên nhân rời bỏ.
                                * **Ưu đãi:** Đưa ra deal giảm giá sâu có giới hạn thời gian cực ngắn để thúc đẩy họ quay trở lại mua sắm.
                                """)
                            else:
                                st.markdown("""
                                * **Mục tiêu:** Nuôi dưỡng mối quan hệ và duy trì mức độ nhận diện thương hiệu.
                                * **Hành động:** Gửi bản tin xu hướng sản phẩm định kỳ, tặng mã miễn phí vận chuyển cho các đơn hàng nhỏ.
                                """)
        except Exception as file_ex:
            st.error(f"Lỗi đọc file đầu vào: {file_ex}")
