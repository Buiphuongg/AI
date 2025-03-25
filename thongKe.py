from flask import Flask, render_template, Response, url_for, redirect, session, request, send_from_directory, flash, jsonify
from flask import redirect
from flask import Blueprint
import pandas as pd
from flask import send_file
from io import BytesIO

thongKe = Blueprint("thongke",__name__)

from flask import Flask, render_template, request, url_for, redirect, Blueprint
from db import get_db_connection  # Import kết nối từ db.py

thongKe = Blueprint("thongke", __name__)


@thongKe.route('/thongke')
def thongke():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Truy vấn dữ liệu chính
    cur.execute("""
        SELECT dl.ma_khay_hang, SUM(dl.so_luong_hu_hong), kh.so_luong_trong_khay, kh.ten_khay_hang 
        FROM dulieuhinhanh dl 
        LEFT JOIN khayhang kh ON dl.ma_khay_hang = kh.ma_khay_hang
        GROUP BY dl.ma_khay_hang, kh.so_luong_trong_khay, kh.ten_khay_hang
    """)
    data1 = cur.fetchall()  # Đọc hết dữ liệu trước khi thực hiện truy vấn mới

    # Truy vấn tổng số lượng hư hỏng
    cur.execute("SELECT SUM(so_luong_hu_hong) FROM dulieuhinhanh")
    data2 = cur.fetchone()  # Đọc dữ liệu
    data2 = data2[0] if data2 and data2[0] is not None else 0  # Xử lý None

    # Truy vấn tổng số lượng trong khay
    cur.execute("""
        SELECT SUM(so_luong_trong_khay) FROM khayhang
    """)
    data3 = cur.fetchone()  # Đọc dữ liệu
    data3 = data3[0] if data3 and data3[0] is not None else 0  # Xử lý None

    # Tính số lượng bình thường
    binhthuong = int(data3) - int(data2)

    cur.close()
    conn.close()

    # Xác định quyền để chọn template phù hợp
    ma_quyen = session.get('ma_quyen', '2')
    template_folder = "admin" if ma_quyen == '0' else "manager" if ma_quyen == '1' else "user"

    return render_template(f"{template_folder}/thongKe.html", thongke=data1, traicay=data3, huhong=data2,binhthuong=binhthuong)


@thongKe.route('/export_report')
def xuatbaocao():
    conn = get_db_connection()
    cur = conn.cursor()

    # Lấy dữ liệu từ cơ sở dữ liệu
    cur.execute("""
        SELECT kh.ma_khay_hang, kh.ten_khay_hang,COALESCE(SUM(dl.so_luong_hu_hong), 0), kh.so_luong_trong_khay 
        FROM khayhang kh
        LEFT JOIN dulieuhinhanh dl ON kh.ma_khay_hang = dl.ma_khay_hang
        GROUP BY kh.ma_khay_hang, kh.so_luong_trong_khay, kh.ten_khay_hang
    """)
    data = cur.fetchall()

    cur.close()
    conn.close()

    # Chuyển dữ liệu thành DataFrame
    df = pd.DataFrame(data, columns=["Khay Hàng","Tên Khay", "Số Lượng Hư Hỏng", "Số Lượng Tổng"])

    # Tạo file Excel trong bộ nhớ
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Thống kê", index=False)
    output.seek(0)

    # Gửi file về client
    return send_file(output, as_attachment=True, download_name="BaoCao_ThongKe.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")