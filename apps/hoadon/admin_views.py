from django.shortcuts import render, redirect

def hoadon_list(request):
    return render(request, 'admin/dashboard/dashboard.html')