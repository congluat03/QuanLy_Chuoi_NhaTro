document.addEventListener('DOMContentLoaded', function () {
    var phongSelect = document.getElementById('MA_PHONG');
    
    if (phongSelect) {
        phongSelect.addEventListener('change', function () {

            const maPhong = this.value;
            alert(maPhong);
            if (maPhong) {
                // Gửi yêu cầu AJAX để kiểm tra cọc phòng
                fetch(`/admin/hopdong/kiem-tra-coc-phong/${maPhong}/`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    
                    if (data.success && data.coc_phong) {
                        
                        // Điền thông tin tiền cọc
                        document.getElementById('TIEN_COC_PHONG').value = data.coc_phong.TIEN_COC_PHONG || '';
                        
                        document.getElementById('GIA_THUE').value = data.coc_phong.TIEN_PHONG || '';
                        // Điền thông tin khách thuê
                        document.getElementById('MA_KHACH_THUE').value = data.coc_phong.MA_KHACH_THUE.MA_KHACH_THUE || '';
                        document.getElementById('HO_TEN_KT').value = data.coc_phong.MA_KHACH_THUE.HO_TEN_KT || '';
                        document.getElementById('GIOI_TINH_KT').value = data.coc_phong.MA_KHACH_THUE.GIOI_TINH_KT || '';
                        document.getElementById('NGAY_SINH_KT').value = data.coc_phong.MA_KHACH_THUE.NGAY_SINH_KT || '';
                        document.getElementById('SDT_KT').value = data.coc_phong.MA_KHACH_THUE.SDT_KT || '';
                        document.getElementById('SO_CMND_CCCD').value = data.coc_phong.MA_KHACH_THUE.SO_CMND_CCCD || '';                        
                    } else {
                        // Xóa các input nếu không có cọc phòng hợp lệ
                        document.getElementById('TIEN_COC_PHONG').value = '';
                        document.getElementById('MA_KHACH_THUE').value = '';
                        document.getElementById('HO_TEN_KT').value = '';
                        document.getElementById('GIOI_TINH_KT').value = '';
                        document.getElementById('NGAY_SINH_KT').value = '';
                        document.getElementById('SDT_KT').value = '';
                        document.getElementById('SO_CMND_CCCD').value = '';                   
                    }
                })
                .catch(error => {
                    console.error('Lỗi khi kiểm tra cọc phòng:', error);
                    // Xóa các input nếu có lỗi
                    document.getElementById('TIEN_COC_PHONG').value = '';
                    document.getElementById('MA_KHACH_THUE').value = '';
                    document.getElementById('HO_TEN_KT').value = '';
                    document.getElementById('GIOI_TINH_KT').value = '';
                    document.getElementById('NGAY_SINH_KT').value = '';
                    document.getElementById('SDT_KT').value = '';
                    document.getElementById('SO_CMND_CCCD').value = '';
                });
            }
        });
    }
});

// Hàm lấy CSRF token từ cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
