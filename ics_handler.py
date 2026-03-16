# ics_handler.py
from datetime import datetime, timedelta

def generate_ics_content(selected_courses_dict, tet_start, tet_end):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PTIT Schedule Tool//VN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Thời Khóa Biểu PTIT",
        "X-WR-TIMEZONE:Asia/Ho_Chi_Minh"
    ]

    # Bộ từ điển chuyển đổi Tiết -> Giờ chuẩn
    time_map = {
        1: (7, 0), 2: (7, 50), 3: (8, 40), 4: (9, 30), 5: (10, 20), 6: (11, 10),
        7: (13, 0), 8: (13, 50), 9: (14, 40), 10: (15, 30), 11: (16, 20), 12: (17, 10)
    }

    for row_id, course in selected_courses_dict.items():
        start_date_str = course.get("Ngày Học")
        tiet_bat_dau = int(course.get("Tiết Bắt Đầu", 1))
        so_tiet = int(course.get("Số Tiết", 2))
        so_tin_chi = int(course.get("Số Tín Chỉ", 3))

        # Tính toán tổng số tuần học dựa trên tín chỉ
        try:
            total_weeks = int((so_tin_chi * 15) / so_tiet)
            if total_weeks < 1: total_weeks = 15
        except:
            total_weeks = 15 # Mặc định an toàn

        start_h, start_m = time_map.get(tiet_bat_dau, (7, 0))
        duration = timedelta(minutes=so_tiet * 50)

        try:
            base_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except:
            continue

        weeks_added = 0
        current_date = base_date

        # Vòng lặp sinh sự kiện cho từng tuần
        while weeks_added < total_weeks:
            # Thuật toán "Né" nghỉ Tết
            if tet_start <= current_date.date() <= tet_end:
                current_date += timedelta(days=7)
                continue

            start_dt = current_date.replace(hour=start_h, minute=start_m)
            end_dt = start_dt + duration

            # Convert sang giờ UTC (Trừ 7 tiếng)
            start_dt_utc = start_dt - timedelta(hours=7)
            end_dt_utc = end_dt - timedelta(hours=7)

            dtstart = start_dt_utc.strftime("%Y%m%dT%H%M%SZ")
            dtend = end_dt_utc.strftime("%Y%m%dT%H%M%SZ")

            summary = f"{course.get('Tên Môn', '')} - {course.get('Mã Lớp', '')}"
            loc = course.get('Phòng', '')
            desc = f"Giảng viên: {course.get('Giảng Viên', '')}\\nMã môn: {course.get('Mã Môn', '')}\\nTín chỉ: {so_tin_chi}"

            lines.extend([
                "BEGIN:VEVENT",
                f"SUMMARY:{summary}",
                f"LOCATION:{loc}",
                f"DESCRIPTION:{desc}",
                f"DTSTART:{dtstart}",
                f"DTEND:{dtend}",
                "END:VEVENT"
            ])

            weeks_added += 1
            current_date += timedelta(days=7)

    lines.append("END:VCALENDAR")
    return "\n".join(lines)