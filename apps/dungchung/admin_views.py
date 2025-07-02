from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm



def dashboard(request):
    return render(request, 'admin/dashboard/dashboard.html')

def doi_mat_khau(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Bạn cần đăng nhập để đổi mật khẩu.')
        return redirect('index:login')  # Adjust to your login URL

    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # Keep user logged in
            messages.success(request, 'Đổi mật khẩu thành công!')
            return redirect('thanhvien:profile')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
            return render(request, 'admin/quanly/profile.html', {
                'form_data': request.POST,
                'form_errors': form.errors,
            })

    return render(request, 'admin/quanly/profile.html', {
        'form_data': {},
        'form_errors': {},
    })

def profile(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Bạn cần đăng nhập để xem hồ sơ.')
        return redirect('index:login')  # Adjust to your login URL

    return render(request, 'admin/trangcanhan/thongtin_canhan.html', {
        'form_data': {},
        'form_errors': {},
    })