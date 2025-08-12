 // Hàm lấy CSRF token
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

    var phongSelect = document.getElementById('MA_PHONG');
    var serviceTableBody = document.querySelector('#service-details');
    var tienPhongInput = document.getElementById('TIEN_PHONG');
    var tienDichVuInput = document.getElementById('TIEN_DICH_VU');
    var tienCocInput = document.getElementById('TIEN_COC');

    var dichVuRows = document.querySelectorAll('#service-details tr');
    updateTongTien();
    dichVuRows.forEach((row, index) => {
        var maChiSo = row.id.replace('dichvu-', '') || index;
        var chiSoCuInput = document.getElementById(`CHISOCU-${index}`);
        var chiSoMoiInput = document.getElementById(`CHISOMOI-${index}`);
        var soDichVuInput = document.getElementById(`SODICHVUTONG-${index}`);
        var thanhTienInput = document.getElementById(`TIENDICHVUGHIDUOC-${index}`);

        if (!chiSoCuInput || !chiSoMoiInput || !soDichVuInput || !thanhTienInput) return;

        // Kiểm tra xem dịch vụ này có bị khóa chỉnh sửa không
        var isReadOnly = chiSoMoiInput.hasAttribute('readonly');

        // Nếu được chỉnh sửa, thêm sự kiện
        if (!isReadOnly) {
            chiSoMoiInput.addEventListener('input', () => {
                var chiSoCu = parseFloat(chiSoCuInput.value) || 0;
                var chiSoMoi = parseFloat(chiSoMoiInput.value) || 0;

                var soDichVu = chiSoMoi - chiSoCu;
                var giaDichVu = parseFloat(row.getAttribute('data-gia-dich-vu')) || 0;
                var thanhTien = soDichVu * giaDichVu;

                soDichVuInput.value = soDichVu.toFixed(2);
                thanhTienInput.value = thanhTien.toFixed(2);

                updateTongTienDichVu();
            });
        }
    });

// Hàm cập nhật tổng tiền dịch vụ – bạn có thể điều chỉnh nếu cần cộng dồn
function updateTongTienDichVu() {
    let total = 0;
    const tienInputs = document.querySelectorAll('[id^="TIENDICHVUGHIDUOC-"]');
    tienInputs.forEach(input => {
        total += parseFloat(input.value) || 0;
    });

    const totalField = document.getElementById('tong-tien-dich-vu');
    if (totalField) {
        totalField.textContent = total.toFixed(2);
    }
    updateTongTien();
}
function updateTongTien() {
    const tienPhong = parseFloat(document.getElementById('TIEN_PHONG').value) || 0;

    // Tính tổng tiền dịch vụ từ tất cả các input tiền dịch vụ
    let tienDichVu = 0;
    document.querySelectorAll('[id^="TIENDICHVUGHIDUOC-"]').forEach(input => {
        tienDichVu += parseFloat(input.value) || 0;
    });
    const tienCoc = parseFloat(document.getElementById('TIEN_COC').value) || 0;
    const tienKhauTru = parseFloat(document.getElementById('TIEN_KHAU_TRU').value) || 0;

    tienDichVuInput.value = tienDichVu.toFixed(2);

    const tongTien = tienPhong + tienDichVu + tienCoc + tienKhauTru;
    document.getElementById('TONG_TIEN').value = tongTien.toFixed(2);
}

