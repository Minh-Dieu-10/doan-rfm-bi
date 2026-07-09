import streamlit as st

st.set_page_config(page_title="CRM Analytics System", page_icon="📈", layout="wide")

st.title("🏛️ Hệ Thống CRM Phân Tích Phân Khúc Khách Hàng & Đề Xuất Sản Phẩm")
st.subheader("Đồ án Hệ thống Thông tin Quản lý (MIS)")

st.markdown("""
Chào mừng bạn đến với ứng dụng quản trị quan hệ khách hàng thông minh. Hệ thống được xây dựng nhằm giải quyết bài toán tối ưu hóa chiến lược tiếp thị và gia tăng doanh số thông qua khai phá dữ liệu hành vi.

### Đọc các chức năng chính của hệ thống tại thanh bên trái:
1. **📂 Upload Data**: Nhận file lịch sử giao dịch thô, tự động xử lý sạch, chạy mô hình định lượng **RFM**, phân cụm bằng thuật toán học không giám sát **K-Means**, khai phá luật kết hợp **Apriori** và đồng bộ lên Cloud Database (Supabase).
2. **👤 Customers**: Dashboard theo dõi các nhóm khách hàng sau phân khúc (Champions, Loyal, At Risk...).
3. **🛒 Recommendations**: Giao diện gợi ý chéo sản phẩm thông minh dựa trên lịch sử mua sắm thực tế của toàn hệ thống.

---
### 🛠️ Kiến Trúc Hệ Thống Sử Dụng:
- **Frontend / Dashboard UI:** Streamlit Web Framework
- **Data Engine:** Pandas, Scikit-learn (K-Means), Mlxtend (Apriori)
- **Database Cloud:** PostgreSQL thông qua Supabase Platform
""")

st.info("💡 Mẹo bảo vệ đồ án: Hãy bắt đầu bằng cách vào mục 'Upload Data' ở thanh menu bên trái để tải tệp dữ liệu mẫu lên trước nhé!")
