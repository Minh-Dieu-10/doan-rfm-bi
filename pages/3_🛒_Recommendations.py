import streamlit as st
import pandas as pd
from utils.db import supabase

st.set_page_config(page_title="Gợi ý sản phẩm", page_icon="🛒", layout="wide")
st.title("🛒 Hệ thống Đề xuất sản phẩm (Apriori)")

st.markdown("""
Hệ thống sử dụng thuật toán **Apriori** để tìm kiếm các sản phẩm thường được mua cùng nhau, từ đó tự động gợi ý sản phẩm đi kèm khi khách hàng lựa chọn một mặt hàng cụ thể.
""")

try:
    response = supabase.table("recommendations").select("*").execute()
    data = response.data
    
    if not data:
        st.warning("Chưa có dữ liệu luật kết hợp. Vui lòng upload dữ liệu ở trang Upload Data!")
    else:
        df_rules = pd.DataFrame(data)
        
        # Tách danh sách các sản phẩm làm mồi (antecedents) độc nhất để làm menu chọn
        all_antecedents = sorted(df_rules["antecedents"].unique().tolist())
        
        st.subheader("🔮 Thử nghiệm gợi ý sản phẩm")
        selected_item = st.selectbox("Chọn sản phẩm khách hàng đang xem hoặc bỏ vào giỏ:", all_antecedents)
        
        if selected_item:
            # Lọc ra các luật chứa sản phẩm này
            matched_rules = df_rules[df_rules["antecedents"] == selected_item].copy()
            
            if not matched_rules.empty:
                st.success(f"Tìm thấy {len(matched_rules)} gợi ý phù hợp!")
                
                # Sắp xếp theo Confidence hoặc Lift
                matched_rules = matched_rules.sort_values(by="confidence", ascending=False)
                
                # Hiển thị kết quả gợi ý dạng danh sách/bảng gọn đẹp
                st.write("### Các sản phẩm gợi ý đi kèm lý tưởng nhất:")
                for index, row in matched_rules.head(5).iterrows():
                    with st.container():
                        st.markdown(f"👉 **Nên gợi ý mua thêm:** `{row['consequents']}`")
                        st.caption(f"Độ tin cậy (Confidence): {row['confidence']*100:.1f}% | Chỉ số nâng cao (Lift): {row['lift']:.2f}")
                        st.divider()
            else:
                st.info("Sản phẩm này chưa có đủ dữ liệu hành vi lịch sử để sinh luật gợi ý đạt độ tin cậy tối thiểu.")
        
        # --- HIỂN THỊ TOÀN BỘ TẬP LUẬT ---
        st.divider()
        st.subheader("📋 Danh sách toàn bộ luật kết hợp khai phá được")
        st.dataframe(df_rules[["antecedents", "consequents", "support", "confidence", "lift"]].sort_values(by="lift", ascending=False))

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
