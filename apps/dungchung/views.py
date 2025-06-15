# Views
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django import forms
from apps.thanhvien.models import TaiKhoan

def trang_chu(request):
    return render(request, 'index/trangchu/trangchu.html')

def register_view(request):
    return render(request, 'index/dangkythanhvien/dangkythanhvien.html')


def login_view(request):
    if request.method == 'POST':
        tentai_khoan = request.POST.get('TENTAIKHOAN')
        mat_khau = request.POST.get('MATKHAU')
        
        try:
            # Lấy thông tin tài khoản từ model TaiKhoan
            user = TaiKhoan.objects.get(TAI_KHOAN=tentai_khoan)
            # Kiểm tra mật khẩu
            if user.check_mat_khau(mat_khau):
                # Kiểm tra trạng thái tài khoản
                if user.TRANG_THAI_TK:
                    # Lưu thông tin vào session
                    request.session['user_id'] = user.MA_TAI_KHOAN
                    request.session['username'] = user.TAI_KHOAN
                    request.session['vai_tro'] = user.QUYEN_HAN
                    
                    # Điều hướng dựa trên vai trò
                    if user.QUYEN_HAN == 'admin':
                        return redirect('admin')  # Chuyển hướng đến trang quản lý admin
                    else:
                        return redirect('/')  # Chuyển hướng đến trang mặc định
                else:
                    messages.error(request, 'Tài khoản đã bị khóa.')
            else:
                messages.error(request, 'Mật khẩu không đúng.')
        except TaiKhoan.DoesNotExist:
            messages.error(request, 'Tài khoản không tồn tại.')
        
        # Nếu có lỗi, render lại trang đăng nhập
        return render(request, 'auth/login.html')
    
    # Nếu không phải POST, render trang đăng nhập
    return render(request, 'auth/login.html')