// Hóa đơn Interface JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadKhuVucs();
    
    // Event listeners
    document.getElementById('filter-area').addEventListener('change', function() {
        loadPhongsByKhuVuc(this.value);
    });
    
    document.getElementById('filter-room').addEventListener('change', function() {
        if (this.value) {
            loadRoomInvoiceInfo(this.value);
        } else {
            clearInvoiceForm();
        }
    });
});

// Load danh sách khu vực
function loadKhuVucs() {
    fetch('/hoadon/api/khu-vuc-list/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const selectElement = document.getElementById('filter-area');
                selectElement.innerHTML = '<option value="">Chọn khu vực</option>';
                data.khu_vucs.forEach(kv => {
                    selectElement.innerHTML += `<option value="${kv.MA_KHU_VUC}">${kv.TEN_KHU_VUC}</option>`;
                });
            } else {
                console.error('Lỗi khi load khu vực:', data.error);
            }
        })
        .catch(error => {
            console.error('Lỗi fetch khu vực:', error);
        });
}

// Load danh sách phòng theo khu vực
function loadPhongsByKhuVuc(khuVucId) {
    const roomSelect = document.getElementById('filter-room');
    roomSelect.innerHTML = '<option value="">Chọn phòng</option>';
    
    if (!khuVucId) {
        clearInvoiceForm();
        return;
    }
    
    fetch(`/hoadon/api/phong-theo-khu-vuc/?khu_vuc_id=${khuVucId}`)
        .then(response => response.json())
        .then(data => {
            if (data.phong_tros && data.phong_tros.length > 0) {
                data.phong_tros.forEach(phong => {
                    roomSelect.innerHTML += `<option value="${phong.MA_PHONG}">${phong.TEN_PHONG}</option>`;
                });
            } else if (data.error) {
                console.error('Lỗi khi load phòng:', data.error);
            }
        })
        .catch(error => {
            console.error('Lỗi fetch phòng:', error);
        });
}

// Load thông tin phòng để lập hóa đơn
function loadRoomInvoiceInfo(maPhong) {
    const thangHoaDon = document.getElementById('NGAY_LAP_HDON').value;
    const thangParam = thangHoaDon ? `?thang_hoa_don=${thangHoaDon.substring(0, 7)}` : '';
    
    fetch(`/hoadon/api/thong-tin-phong-hoa-don/${maPhong}/${thangParam}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateInvoiceForm(data);
            } else {
                alert('Lỗi: ' + data.error);
                clearInvoiceForm();
            }
        })
        .catch(error => {
            console.error('Lỗi fetch thông tin phòng:', error);
            clearInvoiceForm();
        });
}

// Điền thông tin vào form hóa đơn
function populateInvoiceForm(data) {
    // Thông tin cơ bản
    document.getElementById('MA_PHONG').value = data.phong_info.MA_PHONG;
    document.getElementById('TIEN_PHONG').value = data.hop_dong.GIA_THUE;
    document.getElementById('TIEN_COC').value = data.hop_dong.GIA_COC_HD;
    document.getElementById('MA_HOP_DONG').value = data.hop_dong.MA_HOP_DONG;
    
    // Thông tin dịch vụ
    populateServiceTable(data.dich_vu_list);
    
    // Tính toán tổng tiền dịch vụ
    calculateServiceTotal();
    calculateTotalInvoice();
}

// Điền bảng dịch vụ
function populateServiceTable(dichVuList) {
    const tbody = document.getElementById('service-details');
    tbody.innerHTML = '';
    
    if (dichVuList && dichVuList.length > 0) {
        document.getElementById('no-service-message').classList.add('hidden');
        
        dichVuList.forEach((dv, index) => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 transition duration-200 border-b border-gray-100';
            row.innerHTML = `
                <td class="p-2 text-center text-gray-700 text-sm">${index + 1}</td>
                <td class="p-2 text-center text-gray-800 text-sm font-medium">${dv.TEN_DICH_VU}</td>
                <td class="p-2 text-center">
                    <input type="number" step="0.01" value="${dv.CHI_SO_CU || 0}" 
                           class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-gray-100" readonly>
                    <input type="hidden" name="chi_so_dich_vu[${index}][CHI_SO_CU]" value="${dv.CHI_SO_CU || 0}">
                </td>
                <td class="p-2 text-center">
                    <input type="number" step="0.01" value="${dv.CHI_SO_MOI || 0}" 
                           class="chi-so-moi w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm focus:ring-2 focus:ring-blue-500"
                           onchange="calculateServiceRow(${index})">
                    <input type="hidden" name="chi_so_dich_vu[${index}][CHI_SO_MOI]" value="${dv.CHI_SO_MOI || 0}">
                </td>
                <td class="p-2 text-center">
                    <input type="number" step="0.01" value="${dv.SO_DICH_VU || 0}" 
                           class="so-dich-vu w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-gray-100" readonly>
                    <input type="hidden" name="chi_so_dich_vu[${index}][SO_DICH_VU]" value="${dv.SO_DICH_VU || 0}">
                </td>
                <td class="p-2 text-center text-gray-700 text-sm">${parseFloat(dv.GIA_DICH_VU || 0).toLocaleString('vi-VN')} đ</td>
                <td class="p-2 text-center">
                    <input type="number" step="0.01" value="${dv.THANH_TIEN || 0}" 
                           class="thanh-tien w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-gray-100" readonly>
                    <input type="hidden" name="chi_so_dich_vu[${index}][THANH_TIEN]" value="${dv.THANH_TIEN || 0}">
                </td>
                <input type="hidden" name="chi_so_dich_vu[${index}][MA_DICH_VU]" value="${dv.MA_DICH_VU}">
                <input type="hidden" name="chi_so_dich_vu[${index}][MA_CHI_SO]" value="${dv.MA_CHI_SO || ''}">
            `;
            tbody.appendChild(row);
        });
    } else {
        document.getElementById('no-service-message').classList.remove('hidden');
    }
}

// Tính toán cho từng dòng dịch vụ
function calculateServiceRow(index) {
    const row = document.querySelector(`#service-details tr:nth-child(${index + 1})`);
    if (!row) return;
    
    const chiSoCu = parseFloat(row.querySelector('input[name*="[CHI_SO_CU]"]').value) || 0;
    const chiSoMoi = parseFloat(row.querySelector('.chi-so-moi').value) || 0;
    const giaDichVu = parseFloat(row.cells[5].textContent.replace(/[^\d.]/g, '')) || 0;
    
    const soDichVu = chiSoMoi - chiSoCu;
    const thanhTien = soDichVu * giaDichVu;
    
    // Cập nhật giá trị hiển thị
    row.querySelector('.so-dich-vu').value = soDichVu;
    row.querySelector('.thanh-tien').value = thanhTien;
    
    // Cập nhật hidden inputs
    row.querySelector('input[name*="[CHI_SO_MOI]"]').value = chiSoMoi;
    row.querySelector('input[name*="[SO_DICH_VU]"]').value = soDichVu;
    row.querySelector('input[name*="[THANH_TIEN]"]').value = thanhTien;
    
    // Tính lại tổng tiền dịch vụ
    calculateServiceTotal();
    calculateTotalInvoice();
}

// Tính tổng tiền dịch vụ
function calculateServiceTotal() {
    const thanhTienElements = document.querySelectorAll('.thanh-tien');
    let total = 0;
    thanhTienElements.forEach(el => {
        total += parseFloat(el.value) || 0;
    });
    document.getElementById('TIEN_DICH_VU').value = total.toFixed(2);
}

// Xóa form hóa đơn
function clearInvoiceForm() {
    document.getElementById('MA_PHONG').value = '';
    document.getElementById('TIEN_PHONG').value = '';
    document.getElementById('TIEN_COC').value = '';
    document.getElementById('TIEN_DICH_VU').value = '';
    document.getElementById('TIEN_KHAU_TRU').value = '';
    document.getElementById('TONG_TIEN').value = '';
    document.getElementById('MA_HOP_DONG').value = '';
    
    // Xóa bảng dịch vụ
    document.getElementById('service-details').innerHTML = '';
    document.getElementById('no-service-message').classList.remove('hidden');
    
    // Xóa bảng khấu trừ
    document.getElementById('discount-details').innerHTML = '';
    document.getElementById('no-deduction-message').classList.remove('hidden');
}