from django.shortcuts import render, redirect

def hopdong_list(request):
    return render(request, 'admin/dashboard/dashboard.html')