import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from ics_handler import generate_ics_content # Import hàm từ file mới

# 1. CẤU HÌNH GIAO DIỆN & STATE
st.set_page_config(page_title="Tra cứu TKB", layout="wide")
st.title("📚 Công cụ Lọc và Xếp Lịch Học PTIT")

if 'selected_dict' not in st.session_state:
    st.session_state.selected_dict = {}
if 'current_search_results' not in st.session_state:
    st.session_state.current_search_results = pd.DataFrame()
if 'current_cart_results' not in st.session_state:
    st.session_state.current_cart_results = pd.DataFrame()

# 2. CALLBACKS CHỐNG KẸT CLICK
def update_cart():
    changes = st.session_state.search_table.get("edited_rows", {})
    df_prev = st.session_state.current_search_results
    for row_idx, edit in changes.items():
        if "Chọn" in edit:
            if row_idx < len(df_prev):
                row_data = df_prev.iloc[row_idx]
                row_id = row_data['ID_Lop']
                if edit["Chọn"]: st.session_state.selected_dict[row_id] = row_data.to_dict()
                else: st.session_state.selected_dict.pop(row_id, None)

def remove_from_cart():
    changes = st.session_state.cart_table.get("edited_rows", {})
    df_prev_cart = st.session_state.current_cart_results
    for row_idx, edit in changes.items():
        if "Chọn" in edit and not edit["Chọn"]:
            if row_idx < len(df_prev_cart):
                row_id = df_prev_cart.iloc[row_idx]['ID_Lop']
                st.session_state.selected_dict.pop(row_id, None)

# 3. SIDEBAR CẤU HÌNH NGHỈ TẾT
with st.sidebar:
    st.header("⚙️ Cấu hình Lịch nghỉ")
    st.write("Cài đặt khoảng thời gian nghỉ Tết. Hệ thống sẽ tự động bỏ qua các ngày này khi tạo lịch.")
    tet_start_date = st.date_input("Nghỉ Tết từ ngày:", datetime(2026, 2, 9))
    tet_end_date = st.date_input("Đến hết ngày:", datetime(2026, 2, 22))

# 4. KẾT NỐI DATABASE VÀ GIAO DIỆN TÌM KIẾM
@st.cache_resource
def get_connection():
    return sqlite3.connect('truong_ptit.db', check_same_thread=False)

conn = get_connection()

st.subheader("🔍 Tìm kiếm môn học")
col1, col2, col3 = st.columns(3)
with col1: ten_mon = st.text_input("Tên môn học (VD: Lập trình Web)")
with col2: ma_mon = st.text_input("Mã môn học (VD: INT1434)")
with col3: giang_vien = st.text_input("Giảng viên")

col4, col5 = st.columns(2)
with col4: thu = st.selectbox("Thứ", ["Tất cả", "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"])
with col5: ma_lop = st.text_input("Mã Lớp (VD: D23CQCN01-N)")

query = "SELECT * FROM thoi_khoa_bieu WHERE 1=1"
params = []

if ten_mon: query += " AND [Tên Môn] LIKE ?"; params.append(f'%{ten_mon}%')
if ma_mon: query += " AND [Mã Môn] LIKE ?"; params.append(f'%{ma_mon}%')
if giang_vien: query += " AND [Giảng Viên] LIKE ?"; params.append(f'%{giang_vien}%')
if ma_lop: query += " AND [Mã Lớp] LIKE ?"; params.append(f'%{ma_lop}%')
if thu != "Tất cả": query += " AND [Thứ] = ?"; params.append(thu)

try:
    df_results = pd.read_sql_query(query, conn, params=params)
    if not df_results.empty:
        st.write(f"**Tìm thấy {len(df_results)} kết quả:**")
        
        df_results['ID_Lop'] = df_results['Mã Môn'].astype(str) + "_" + df_results['Mã Lớp'].astype(str)
        df_results.insert(0, "Chọn", df_results["ID_Lop"].isin(st.session_state.selected_dict.keys()))
        
        st.session_state.current_search_results = df_results
        
        st.data_editor(
            df_results,
            column_config={
                "Chọn": st.column_config.CheckboxColumn("Chọn", help="Tick để lưu", default=False),
                "ID_Lop": None 
            },
            disabled=[col for col in df_results.columns if col not in ["Chọn"]], 
            hide_index=True, use_container_width=True, key="search_table", on_change=update_cart
        )
    else:
        st.info("Không tìm thấy môn học nào phù hợp với từ khóa.")
except Exception as e:
    st.error(f"Lỗi truy vấn Database: {e}")

# 5. HIỂN THỊ GIỎ HÀNG VÀ XUẤT FILE ICS
st.divider()
st.subheader("🛒 Danh sách các môn đã chọn")

if st.session_state.selected_dict:
    df_selected = pd.DataFrame(list(st.session_state.selected_dict.values()))
    df_selected['Chọn'] = True
    
    st.session_state.current_cart_results = df_selected
    
    st.data_editor(
        df_selected,
        column_config={
            "Chọn": st.column_config.CheckboxColumn("Đã chọn", help="Bỏ tick để xóa", default=True),
            "ID_Lop": None
        },
        disabled=[col for col in df_selected.columns if col not in ["Chọn"]],
        hide_index=True, use_container_width=True, key="cart_table", on_change=remove_from_cart
    )
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🗑️ Xóa tất cả danh sách"):
            st.session_state.selected_dict = {}
            st.rerun()
            
    with col_btn2:
        # Sử dụng hàm đã import
        ics_content = generate_ics_content(
            st.session_state.selected_dict, 
            tet_start_date, 
            tet_end_date
        )
        
        st.download_button(
            label="📅 Tải xuống file .ics",
            data=ics_content,
            file_name="thoikhoabieu_ptit.ics",
            mime="text/calendar",
            type="primary"
        )
else:
    st.info("Danh sách chờ đang trống. Hãy tick chọn môn học ở bảng tìm kiếm!")