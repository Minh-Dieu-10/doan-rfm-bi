import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- THÔNG TIN KẾT NỐI API SUPABASE ---
# Lấy từ phần Project API (URL và anon key) của bạn
SUPABASE_URL = "https://cylljidqxzublpipypcu.supabase.co"
SUPABASE_KEY = "sb_publishable_3DEP2QBBrM7uT0AZmj4Wpw_9fcnn8h6"

# Khởi tạo kết nối qua API
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Lỗi khởi tạo Supabase Client: {e}")

# --- CHƯƠNG TRÌNH CHÍNH (STREAMLIT APP) ---
st.set_page_config(page_title="Hệ thống Phân tích RFM", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title(" ĐĂNG NHẬP HỆ THỐNG")
    username = st.text_input("Tài khoản admin")
    password = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if username == "admin" and password == "123456":
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Sai tài khoản hoặc mật khẩu!")
else:
    st.title(" HỆ THỐNG XỬ LÝ DỮ LIỆU & PHÂN TÍCH RFM KHÁCH HÀNG")
    st.sidebar.button("Đăng xuất", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    st.subheader(" Bước 1: Nạp file dữ liệu bán hàng")
    uploaded_file = st.file_uploader("Chọn file OnlineRetail (.csv hoặc .xlsx)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
            else:
                df = pd.read_excel(uploaded_file)
                
            st.success(f"Đã tải file thành công! Số lượng bản ghi: {len(df):,}")
            st.dataframe(df.head(5))
            
            st.subheader(" Bước 2: Kích hoạt quy trình xử lý dữ liệu (ETL)")
            if st.button("Kích hoạt quy trình ETL"):
                with st.spinner("Đang làm sạch dữ liệu, tính toán RFM và đẩy vào Supabase qua API..."):
                    # 1. Làm sạch dữ liệu
                    df = df.dropna(subset=['CustomerID'])
                    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
                    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
                    df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
                    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
                    
                    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
                    df = df.dropna(subset=['InvoiceDate'])
                    df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
                    
                    # 2. Tính toán RFM
                    current_date = df['InvoiceDate'].max()
                    rfm = df.groupby('CustomerID').agg({
                        'InvoiceDate': lambda x: (current_date - x.max()).days,
                        'InvoiceNo': 'nunique',
                        'TotalAmount': 'sum'
                    }).reset_index()
                    
                    rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
                    
                    try:
                        rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
                        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
                        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
                    except Exception:
                        rfm['R_Score'] = 3; rfm['F_Score'] = 3; rfm['M_Score'] = 3
                        
                    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
                    
                    def segment_rfm(score):
                        r, f, m = int(score[0]), int(score[1]), int(score[2])
                        if r >= 4 and f >= 4 and m >= 4: return 'Champions (VIP)'
                        elif r >= 3 and f >= 3: return 'Loyal Customers'
                        elif r >= 4 and f <= 2: return 'New Customers'
                        elif r <= 2 and f >= 3: return 'At Risk'
                        else: return 'Hibernating / Lost'
                        
                    rfm['RFM_Group'] = rfm['RFM_Score'].apply(segment_rfm)
                    
                    # 3. Đẩy dữ liệu lên Supabase theo cơ chế API Upsert từng cụm (Batch)
                    # Chuyển dữ liệu thành list các object để gửi API
                    records = []
                    for _, row in rfm.iterrows():
                        records.append({
                            "customerid": str(row['CustomerID']),
                            "recency": int(row['Recency']),
                            "frequency": int(row['Frequency']),
                            "monetary": float(row['Monetary']),
                            "rfm_score": str(row['RFM_Score']),
                            "rfm_group": str(row['RFM_Group'])
                        })
                    
                    # Chia nhỏ dữ liệu ra gửi mỗi lần 1000 dòng để tránh quá tải API
                    batch_size = 1000
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i+batch_size]
                        # Thực hiện đẩy dữ liệu (Upsert dựa trên khóa chính customerid)
                        supabase.table("Dim_Customer").upsert(batch).execute()
                        
                    st.success(" Quy trình ETL hoàn tất!")
                    st.balloons()

                    st.write(" Kết quả phân tích phân khúc khách hàng:")
                    st.dataframe(rfm.head(10))
                    
                    # --- BỔ SUNG NÚT DOWNLOAD BÁO CÁO EXCEL / CSV (ĐẶT Ở ĐÂY LÀ CHUẨN) ---
                    st.subheader("Xuất báo cáo phân khúc khách hàng")

                    # 1. Tạo dữ liệu file CSV
                    csv_data = rfm.to_csv(index=False).encode('utf-8-sig')

                    # 2. Tạo dữ liệu file Excel bằng BytesIO
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        rfm.to_excel(writer, index=False, sheet_name='RFM Segment')
                    excel_data = buffer.getvalue()

                    # 3. Hiển thị 2 nút bấm tải file trên giao diện (chia làm 2 cột)
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
        except Exception as ex:
            st.error(f"Có lỗi xảy ra khi xử lý file hoặc đẩy API: {ex}")
