from apps.thanhvien.models import TaiKhoan

class CustomAuthenticationMiddleware:
    """
    Middleware để tạo user object từ session cho custom authentication system
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Kiểm tra session authentication
        if request.session.get('is_authenticated'):
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    request.user = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
                    request.user.is_authenticated = True
                except TaiKhoan.DoesNotExist:
                    request.session.flush()  # Clear invalid session
                    request.user = None
            else:
                request.user = None
        else:
            request.user = None

        response = self.get_response(request)
        return response