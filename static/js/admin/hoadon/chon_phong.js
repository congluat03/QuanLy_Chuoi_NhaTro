document.addEventListener('DOMContentLoaded', function () {
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

    const phongSelect = document.getElementById('MA_PHONG');
    const serviceTableBody = document.querySelector('#service-details');
    const tienPhongInput = document.getElementById('TIEN_PHONG');
    const tienDichVuInput = document.getElementById('TIEN_DICH_VU');
    const tienCocInput = document.getElementById('TIEN_COC');

    if (phongSelect) {
        phongSelect.addEventListener('change', function () {
            const maPhong = this.value;

            if (maPhong) {
                // Gửi yêu cầu AJAX để lấy thông tin hợp đồng, dịch vụ và chỉ số dịch vụ
                fetch(`/admin/hoadon/lay-thong-tin-phong/${maPhong}/`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Cập nhật giá phòng từ hợp đồng
                        tienPhongInput.value = data.hop_dong?.GIA_THUE || '0.00';
                        tienCocInput.value = data.phong_tro?.SO_TIEN_CAN_COC || '0.00';

                        // Xóa bảng dịch vụ hiện tại
                        serviceTableBody.innerHTML = '';

                        // Cập nhật bảng dịch vụ
                        if (data.dich_vu && data.dich_vu.length > 0) {
                            data.dich_vu.forEach((dv, index) => {
                                const isFixedService = dv.LOAI_DICH_VU === 'Cố định';
                                const hasChiSoMoi = dv.CHI_SO_MOI !== null && dv.CHI_SO_MOI !== undefined;
                                const chiSoCu = dv.CHI_SO_CU || '0';
                                const chiSoMoi = dv.CHI_SO_MOI || '0';
                                const soDichVu = dv.SO_DICH_VU || '0';
                                const thanhTien = dv.THANH_TIEN || '0.00';
                                const maDichVu = dv.MA_DICH_VU || '';
                                const maChiSo = dv.MA_CHI_SO || '';

                                // Tạo hàng mới trong bảng dịch vụ
                                const row = document.createElement('tr');
                                row.id = `dichvu-${dv.MA_CHI_SO || index}`;
                                row.className = 'hover:bg-gray-50 transition duration-200 border-b border-gray-100';
                                row.innerHTML = `
                                    <td class="p-2 text-center text-gray-700 text-sm">${index + 1}</td>
                                    <td class="p-2 text-center text-gray-700 text-sm">${dv.TEN_DICH_VU}</td>
                                    <td class="p-2 text-center">
                                        <input type="number" name="CHISOCU[${dv.MA_CHI_SO || index}]" value="${chiSoCu}"
                                            class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500"
                                            id="CHISOCU-${dv.MA_CHI_SO || index}" step="0.01" disabled>
                                    </td>
                                    <td class="p-2 text-center">
                                        <input type="number" name="chi_so_dich_vu[${index}][CHI_SO_MOI]" value="${chiSoMoi}"
                                            class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm focus:ring-2 focus:ring-blue-500"
                                            id="CHISOMOI-${dv.MA_CHI_SO || index}" step="0.01" ${isFixedService || hasChiSoMoi ? 'disabled' : ''}>
                                    </td>
                                    <td class="p-2 text-center">
                                        <input type="number" name="SODICHVUTONG[${dv.MA_CHI_SO || index}]" value="${soDichVu}"
                                            class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500"
                                            id="SODICHVUTONG-${dv.MA_CHI_SO || index}" step="0.01" disabled>
                                    </td>
                                    <td class="p-2 text-center">
                                        <input type="number" name="TIENDICHVUGHIDUOC[${dv.MA_CHI_SO || index}]" value="${thanhTien}"
                                            class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500"
                                            id="TIENDICHVUGHIDUOC-${dv.MA_CHI_SO || index}" step="0.01" disabled>
                                    </td>
                                    <td class="p-2 text-center">
                                        <button type="button" class="bg-blue-600 text-white text-xs font-medium px-2 py-1 rounded-lg hover:bg-blue-700 transition duration-300"
                                            id="button-${dv.MA_CHI_SO || index}" data-status="1" title="Chỉnh sửa">
                                            <i class="fa fa-edit"></i>
                                        </button>
                                    </td>
                                `;
                                serviceTableBody.appendChild(row);
                                // Chỉ thêm hidden inputs nếu có MA_CHI_SO
                                if (!isFixedService) {
                                    const inputs = [
                                        { name: `chi_so_dich_vu[${index}][MA_DICH_VU]`, value: maDichVu },
                                        { name: `chi_so_dich_vu[${index}][MA_CHI_SO]`, value: maChiSo },
                                        { name: `chi_so_dich_vu[${index}][CHI_SO_CU]`, value: chiSoCu },
                                        { name: `chi_so_dich_vu[${index}][CHI_SO_MOI]`, value: chiSoMoi },
                                        { name: `chi_so_dich_vu[${index}][SO_DICH_VU]`, value: soDichVu },
                                        { name: `chi_so_dich_vu[${index}][THANH_TIEN]`, value: thanhTien }
                                    ];

                                    inputs.forEach(input => {
                                        const hiddenInput = document.createElement('input');
                                        hiddenInput.type = 'hidden';
                                        hiddenInput.name = input.name;
                                        hiddenInput.value = input.value;
                                        hiddenInput.id = `hidden_chi_so_dich_vu_${index}_${input.name.split('[').pop().replace(']', '')}`;
                                        serviceTableBody.appendChild(hiddenInput);
                                    });
                                }                              
                                
                                // Thêm sự kiện để tính toán lại số dịch vụ và thành tiền
                                if (!isFixedService && !hasChiSoMoi) {
                                    const chiSoMoiInput = document.getElementById(`CHISOMOI-${dv.MA_CHI_SO || index}`);
                                    chiSoMoiInput.addEventListener('input', () => {
                                        const chiSoCu = parseFloat(document.getElementById(`CHISOCU-${dv.MA_CHI_SO || index}`).value) || 0;
                                        const chiSoMoi = parseFloat(chiSoMoiInput.value) || 0;
                                        const soDichVu = chiSoMoi - chiSoCu;
                                        const thanhTien = soDichVu * (dv.GIA_DICH_VU || 0);

                                        document.getElementById(`SODICHVUTONG-${dv.MA_CHI_SO || index}`).value = soDichVu.toFixed(2);
                                        document.getElementById(`TIENDICHVUGHIDUOC-${dv.MA_CHI_SO || index}`).value = thanhTien.toFixed(2);

                                        // Cập nhật tổng tiền dịch vụ
                                        updateTongTienDichVu();
                                    });
                                }
                            });

                            // Cập nhật tổng tiền dịch vụ
                            updateTongTienDichVu();
                        } else {
                            serviceTableBody.innerHTML = `
                                <tr>
                                    <td colspan="7" class="text-gray-500 text-center py-4 text-sm">Không có thông tin dịch vụ.</td>
                                </tr>`;
                        }
                    } else {
                        // Xóa dữ liệu nếu không có hợp đồng hợp lệ
                        tienPhongInput.value = '0.00';
                        tienCocInput.value = '0.00';
                        tienDichVuInput.value = '0.00';
                        serviceTableBody.innerHTML = `
                            <tr>
                                <td colspan="7" class="text-gray-500 text-center py-4 text-sm">Không có thông tin dịch vụ.</td>
                            </tr>`;
                    }
                })
                .catch(error => {
                    console.error('Lỗi khi lấy thông tin phòng:', error);
                    tienPhongInput.value = '0.00';
                    tienCocInput.value = '0.00';
                    tienDichVuInput.value = '0.00';
                    serviceTableBody.innerHTML = `
                        <tr>
                            <td colspan="7" class="text-gray-500 text-center py-4 text-sm">Không có thông tin dịch vụ.</td>
                        </tr>`;
                });
            }
        });
    }

    // Hàm cập nhật tổng tiền dịch vụ
    function updateTongTienDichVu() {
        let tongTienDichVu = 0;
        document.querySelectorAll('[name^="TIENDICHVUGHIDUOC"]').forEach(input => {
            tongTienDichVu += parseFloat(input.value) || 0;
        });
        tienDichVuInput.value = tongTienDichVu.toFixed(2);

        // Cập nhật tổng tiền hóa đơn
        updateTongTien();
    }

    // Hàm cập nhật tổng tiền hóa đơn
    function updateTongTien() {
        const tienPhong = parseFloat(tienPhongInput.value) || 0;
        const tienDichVu = parseFloat(tienDichVuInput.value) || 0;
        const tienCoc = parseFloat(tienCocInput.value) || 0;
        const tienKhauTru = parseFloat(document.getElementById('TIEN_KHAU_TRU').value) || 0;

        const tongTien = tienPhong + tienDichVu - tienCoc + tienKhauTru;
        document.getElementById('TONG_TIEN').value = tongTien.toFixed(2);
    }

    // Lấy deductionIndex từ data attribute
    const deductionData = document.getElementById('deduction-data');
    let deductionIndex = parseInt(deductionData.dataset.deductionIndex) || 0;

    // Thêm sự kiện cho nút thêm khấu trừ
    const addDeductionBtn = document.getElementById('add-deduction-btn');
    if (addDeductionBtn) {
        addDeductionBtn.addEventListener('click', () => {
            // Logic xử lý thêm khấu trừ (có thể giữ nguyên hoặc điều chỉnh)
            console.log('Khấu trừ mới được thêm, chỉ số hiện tại:', deductionIndex);
        });
    }
});