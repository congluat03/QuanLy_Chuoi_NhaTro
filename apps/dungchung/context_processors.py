from apps.thanhvien.models import TaiKhoan, NguoiQuanLy


def admin_profile_context(request):
    """
    Context processor để cung cấp thông tin admin profile cho tất cả templates
    """
    context = {}
    
    # Kiểm tra nếu user đã đăng nhập và có session
    if request.session.get('is_authenticated'):
        user_id = request.session.get('user_id')
        username = request.session.get('username')
        vai_tro = request.session.get('vai_tro')
        
        # Thêm thông tin cơ bản từ session
        context['current_user'] = {
            'user_id': user_id,
            'username': username,
            'vai_tro': vai_tro,
            'is_admin': vai_tro in ['Chủ trọ', 'admin']
        }
        
        # Lấy thông tin chi tiết nếu là admin/chủ trọ
        if vai_tro in ['Chủ trọ', 'admin'] and user_id:
            try:
                tai_khoan = TaiKhoan.objects.get(MA_TAI_KHOAN=user_id)
                context['current_user']['tai_khoan'] = tai_khoan
                
                try:
                    nguoi_quan_ly = NguoiQuanLy.objects.get(MA_TAI_KHOAN=tai_khoan)
                    context['current_user']['nguoi_quan_ly'] = nguoi_quan_ly
                    context['current_user']['display_name'] = nguoi_quan_ly.TEN_QUAN_LY
                    context['current_user']['email'] = nguoi_quan_ly.EMAIL_QL
                    context['current_user']['phone'] = nguoi_quan_ly.SDT_QUAN_LY
                    context['current_user']['avatar'] = nguoi_quan_ly.ANH_QL
                except NguoiQuanLy.DoesNotExist:
                    context['current_user']['nguoi_quan_ly'] = None
                    context['current_user']['display_name'] = username
                    
            except TaiKhoan.DoesNotExist:
                # Nếu không tìm thấy tài khoản, chỉ dùng thông tin từ session
                pass
    
    return context