import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime

# --- THÔNG TIN KẾT NỐI SUPABASE ---
# Thay thông tin từ supabase vào
DB_HOST = "52.74.252.201"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = "XW55mYXFlwrCFLgt"
DB_PORT = "5432"

# --- HÀM KẾT NỐI DATABASE ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME,
            user=DB_USER, password=DB_PASS, port=DB_PORT
        )
        return conn
    except Exception as e:
        st.error(f"Lỗi kết nối Database: {e}")
        return None

# --- CHƯƠNG TRÌNH CHÍNH (STREAMLIT APP) ---
st.set_page_config(page_title="Hệ thống Phân tích RFM", layout="wide")

# Kiểm tra trạng thái đăng nhập đơn giản
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
    # Giao diện chính sau khi đăng nhập thành công
    st.title(" HỆ THỐNG XỬ LÝ DỮ LIỆU & PHÂN TÍCH RFM KHÁCH HÀNG")
    st.sidebar.button("Đăng xuất", on_click=lambda: st.session_state.update({"logged_in": False}))
    
    st.subheader(" Bước 1: Nạp file dữ liệu bán hàng")
    uploaded_file = st.file_uploader("Chọn file OnlineRetail (.csv hoặc .xlsx)", type=["csv", "xlsx"])
    
    if uploaded_file is not None:
        try:
            # Đọc file dữ liệu
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file, encoding="ISO-8859-1")
            else:
                df = pd.read_excel(uploaded_file)
                
            st.success(f"Đã tải file thành công! Số lượng bản ghi: {len(df):,}")
            st.dataframe(df.head(5))
            
            st.subheader(" Bước 2: Kích hoạt quy trình xử lý dữ liệu (ETL)")
            if st.button("Kích hoạt quy trình ETL"):
                with st.spinner("Đang làm sạch dữ liệu, tính toán RFM và đẩy vào Supabase..."):
                    # 1. Làm sạch dữ liệu cơ bản
                    df = df.dropna(subset=['CustomerID'])
                    df['CustomerID'] = df['CustomerID'].astype(int).astype(str)
                    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
                    df['UnitPrice'] = pd.to_numeric(df['UnitPrice'], errors='coerce')
                    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
                    
                    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
                    df = df.dropna(subset=['InvoiceDate'])
                    df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
                    
                    # 2. Tính toán các chỉ số RFM
                    current_date = df['InvoiceDate'].max()
                    rfm = df.groupby('CustomerID').agg({
                        'InvoiceDate': lambda x: (current_date - x.max()).days,
                        'InvoiceNo': 'nunique',
                        'TotalAmount': 'sum'
                    }).reset_index()
                    
                    rfm.columns = ['CustomerID', 'Recency', 'Frequency', 'Monetary']
                    
                    # Tính điểm từ 1-5 bằng phương pháp chia nhóm (Quantiles)
                    try:
                        rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1])
                        rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5])
                        rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=[1, 2, 3, 4, 5])
                    except Exception:
                        rfm['R_Score'] = 3
                        rfm['F_Score'] = 3
                        rfm['M_Score'] = 3
                        
                    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
                    
                    # Hàm phân nhóm khách hàng đơn giản
                    def segment_rfm(score):
                        r, f, m = int(score[0]), int(score[1]), int(score[2])
                        if r >= 4 and f >= 4 and m >= 4: return 'Champions (VIP)'
                        elif r >= 3 and f >= 3: return 'Loyal Customers'
                        elif r >= 4 and f <= 2: return 'New Customers'
                        elif r <= 2 and f >= 3: return 'At Risk'
                        else: return 'Hibernating / Lost'
                        
                    rfm['RFM_Group'] = rfm['RFM_Score'].apply(segment_rfm)
                    
                    # 3. Kết nối Supabase và tự động tạo bảng, đẩy dữ liệu vào
                    conn = get_db_connection()
                    if conn is not None:
                        cursor = conn.cursor()
                        # Tự động tạo bảng Dim_Customer nếu chưa có
                        cursor.execute("""
                            CREATE TABLE IF NOT EXISTS Dim_Customer (
                                CustomerID VARCHAR(50) PRIMARY KEY,
                                Recency INT,
                                Frequency INT,
                                Monetary FLOAT,
                                RFM_Score VARCHAR(10),
                                RFM_Group VARCHAR(50)
                            );
                        """)
                        conn.commit()
                        
                        # Đổ từng dòng dữ liệu vào bảng
                        for _, row in rfm.iterrows():
                            cursor.execute("""
                                INSERT INTO Dim_Customer (CustomerID, Recency, Frequency, Monetary, RFM_Score, RFM_Group)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (CustomerID) DO UPDATE SET
                                    Recency = EXCLUDED.Recency,
                                    Frequency = EXCLUDED.Frequency,
                                    Monetary = EXCLUDED.Monetary,
                                    RFM_Score = EXCLUDED.RFM_Score,
                                    RFM_Group = EXCLUDED.RFM_Group;
                            """, (row['CustomerID'], int(row['Recency']), int(row['Frequency']), float(row['Monetary']), row['RFM_Score'], row['RFM_Group']))
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        st.success(" Quy trình ETL hoàn tất thành công! Dữ liệu phân nhóm khách hàng đã được đồng bộ tự động lên cơ sở dữ liệu Supabase.")
                        st.balloons()
                        
                        # Hiển thị kết quả vừa lưu
                        st.write(" Kết quả phân tích phân khúc khách hàng (Top 10 dòng đầu):")
                        st.dataframe(rfm.head(10))
        except Exception as ex:
            st.error(f"Có lỗi xảy ra khi xử lý file: {ex}")
