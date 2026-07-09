import streamlit as st

st.set_page_config(page_title="CRM Analytics", page_icon="📈", layout="wide")

st.title("🏛️ Hệ Thống CRM Phân Tích Phân Khúc & Đề Xuất Sản Phẩm")
st.caption("Đồ án Hệ thống Thông tin Quản lý (MIS)")

st.divider()

st.subheader("🛠️ Các chức năng chính:")
st.markdown("""
- **📂 Upload Data**: Tải file giao dịch lên để làm sạch, phân cụm **K-Means** và chạy thuật toán **Apriori**.
- **👤 Customers**: Xem kết quả phân khúc khách hàng (RFM) qua các biểu đồ trực quan.
- **🛒 Recommendations**: Hệ thống thử nghiệm và gợi ý sản phẩm đi kèm khi mua sắm.
""")
