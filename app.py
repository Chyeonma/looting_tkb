import streamlit as st
import sqlite3
import pandas as pd

# 1. Cấu hình giao diện
st.set_page_config(page_title="Tra cứu TKB", layout="wide")
st.title("📚 Công cụ Lọc và Xếp Lịch Học")

# 2. Khởi tạo State để lưu "Danh sách chờ" (Giỏ hàng)
if 'selected_classes' not in st.session_state:
    st.session_state.selected_classes = pd.DataFrame()

# 3. Kết nối Database
# Lưu ý: Sửa lại tên bảng nếu trong db của bạn khác với "thoi_khoa_bieu"
@st.cache_resource
def get_connection():
    return sqlite3.connect('truong_ptit.db', check_same_thread=False)

conn = get_connection()

# 4. Giao diện Tìm kiếm
st.subheader("🔍 Tìm kiếm môn học")
col1, col2, col3 = st.columns(3)

with col1:
    ten_mon = st.text_input("Tên môn học (VD: Lập trình Web)")
with col2:
    ma_mon = st.text_input("Mã môn học (VD: INT1434)")
with col3:
    giang_vien = st.text_input("Giảng viên")

col4, col5 = st.columns(2)
with col4:
    thu = st.selectbox("Thứ", ["Tất cả", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"])
with col5:
    ma_lop = st.text_input("Mã Lớp (VD: D23CQCN01-N)")

# 5. Xây dựng Query linh hoạt dựa trên input
query = "SELECT * FROM thoi_khoa_bieu WHERE 1=1"
params = []

if ten_mon:
    query += " AND [Tên Môn] LIKE ?"
    params.append(f'%{ten_mon}%')
if ma_mon:
    query += " AND [Mã Môn] LIKE ?"
    params.append(f'%{ma_mon}%')
if giang_vien:
    query += " AND [Giảng Viên] LIKE ?"
    params.append(f'%{giang_vien}%')
if ma_lop:
    query += " AND [Mã Lớp] LIKE ?"
    params.append(f'%{ma_lop}%')
if thu != "Tất cả":
    query += " AND [Thứ] = ?"
    params.append(thu)

# Thực thi Query
try:
    df_results = pd.read_sql_query(query, conn, params=params)
    st.write(f"**Tìm thấy {len(df_results)} kết quả:**")
    
    # Hiển thị bảng kết quả và cho phép chọn (Tính năng DataFrame mới của Streamlit)
    event_selection = st.dataframe(
        df_results, 
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row" # Cho phép chọn nhiều hàng cùng lúc
    )
    
    # 6. Nút Thêm vào Danh sách chờ
    selected_indices = event_selection.selection.rows
    if st.button("➕ Thêm môn đã chọn vào danh sách chờ"):
        if selected_indices:
            selected_rows = df_results.iloc[selected_indices]
            # Nối vào danh sách hiện tại và loại bỏ trùng lặp (ví dụ dựa trên Mã Môn + Mã Lớp)
            st.session_state.selected_classes = pd.concat(
                [st.session_state.selected_classes, selected_rows]
            ).drop_duplicates()
            st.success("Đã thêm thành công!")
        else:
            st.warning("Vui lòng chọn ít nhất một môn học từ bảng trên.")

except Exception as e:
    st.error(f"Lỗi truy vấn Database. Hãy kiểm tra lại tên bảng và tên cột. Chi tiết lỗi: {e}")

# 7. Hiển thị Danh sách chờ (Giỏ hàng)
st.divider()
st.subheader("🛒 Danh sách các môn đã chọn")

if not st.session_state.selected_classes.empty:
    st.dataframe(st.session_state.selected_classes, use_container_width=True, hide_index=True)
    
    if st.button("🗑️ Xóa danh sách"):
        st.session_state.selected_classes = pd.DataFrame()
        st.rerun()
    
    # Placeholder cho tính năng xuất file .ics sau này
    st.download_button(
        label="📅 Xuất file .ics (Coming soon)",
        data="Đây sẽ là nội dung file ics",
        file_name="thoikhoabieu.ics",
        mime="text/calendar",
        disabled=True
    )
else:
    st.info("Danh sách chờ đang trống.")