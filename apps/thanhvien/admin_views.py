from django.shortcuts import render, redirect

def nhanvien_list(request):
    return render(request, 'admin/dashboard/dashboard.html')