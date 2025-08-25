
var deductionModal = document.getElementById('deduction-modal');
var modalTitle = document.getElementById('modal-title');
var addDeductionBtn = document.getElementById('add-deduction-btn');
var cancelDeductionBtn = document.getElementById('cancel-deduction');
var saveDeductionBtn = document.getElementById('save-deduction');
var discountDetails = document.getElementById('discount-details');
var noDeductionMessage = document.getElementById('no-deduction-message');
var deductionData = document.getElementById('deduction-data');
var deductionIndex = parseInt(deductionData.dataset.deductionIndex);
var editingDeductionId = null;

addDeductionBtn.addEventListener('click', () => {
    modalTitle.textContent = 'Thêm khấu trừ';
    editingDeductionId = null;
    document.getElementById('modal_NGAYKHAUTRU').value = '';
    document.getElementById('modal_LOAI_KHAU_TRU').value = '';
    document.getElementById('modal_SO_TIEN_KT').value = '';
    document.getElementById('modal_LY_DO_KHAU_TRU').value = '';
    document.querySelectorAll('.text-red-500').forEach(el => el.classList.add('hidden'));
    deductionModal.classList.remove('hidden');
});

cancelDeductionBtn.addEventListener('click', () => {
    deductionModal.classList.add('hidden');
    editingDeductionId = null;
});

saveDeductionBtn.addEventListener('click', () => {
    const ngayKhauTru = document.getElementById('modal_NGAYKHAUTRU').value;
    const loaiKhauTru = document.getElementById('modal_LOAI_KHAU_TRU').value;
    const soTienKt = document.getElementById('modal_SO_TIEN_KT').value;
    const lyDoKhauTru = document.getElementById('modal_LY_DO_KHAU_TRU').value;

    // Validation
    let hasError = false;
    
    // Kiểm tra ngày khấu trừ
    const errorNgay = document.getElementById('error_NGAYKHAUTRU');
    if (errorNgay) {
        errorNgay.classList.toggle('hidden', !!ngayKhauTru);
    }
    if (!ngayKhauTru) hasError = true;
    
    // Kiểm tra loại khấu trừ
    const errorLoai = document.getElementById('error_LOAI_KHAU_TRU');
    if (errorLoai) {
        errorLoai.classList.toggle('hidden', !!loaiKhauTru);
    }
    if (!loaiKhauTru) hasError = true;
    
    // Kiểm tra số tiền
    const errorTien = document.getElementById('error_SO_TIEN_KT');
    if (errorTien) {
        errorTien.classList.toggle('hidden', soTienKt && parseFloat(soTienKt) > 0);
    }
    if (!soTienKt || parseFloat(soTienKt) <= 0) hasError = true;
    
    // Kiểm tra lý do
    const errorLyDo = document.getElementById('error_LY_DO_KHAU_TRU');
    if (errorLyDo) {
        errorLyDo.classList.toggle('hidden', !!lyDoKhauTru);
    }
    if (!lyDoKhauTru) hasError = true;

    if (!hasError) {
        const form = document.getElementById('invoice-form');
        if (editingDeductionId) {
            // Edit existing deduction
            const row = document.getElementById(`khautru_${editingDeductionId}`);
            if (row) {
                row.querySelector(`#loai_khau_tru_${editingDeductionId}`).value = loaiKhauTru;
                row.querySelector(`#so_tien_kt_${editingDeductionId}`).value = parseFloat(soTienKt).toFixed(2);
                row.querySelector(`#ly_do_khau_tru_${editingDeductionId}`).value = lyDoKhauTru;
                row.querySelector(`#ngay_khau_tru_${editingDeductionId}`).value = ngayKhauTru;

                // Update hidden inputs
                const cleanId = editingDeductionId.replace('new_', '');
                const inputs = [
                    { name: `khautru[${cleanId}][NGAYKHAUTRU]`, value: ngayKhauTru },
                    { name: `khautru[${cleanId}][LOAI_KHAU_TRU]`, value: loaiKhauTru },
                    { name: `khautru[${cleanId}][SO_TIEN_KT]`, value: soTienKt },
                    { name: `khautru[${cleanId}][LY_DO_KHAU_TRU]`, value: lyDoKhauTru }
                ];

                inputs.forEach(input => {
                    const hiddenInput = document.getElementById(`hidden_${input.name.replace(/[\[\]]/g, '_')}`);
                    if (hiddenInput) {
                        hiddenInput.value = input.value;
                    }
                });
            }
        } else {
            // Add new deduction
            const rowCount = discountDetails.children.length + 1;
            const newRow = document.createElement('tr');
            newRow.id = `khautru_new_${deductionIndex}`;
            newRow.className = 'hover:bg-gray-50 transition duration-200 border-b border-gray-100';
            newRow.innerHTML = `
                <td class="p-2 text-center text-gray-700 text-sm">${rowCount}</td>
                <td class="p-2 text-center">
                    <select id="loai_khau_tru_new_${deductionIndex}" class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-transparent focus:ring-2 focus:ring-blue-500" disabled>
                        <option value="Cộng" ${loaiKhauTru === 'Cộng' ? 'selected' : ''}>Cộng</option>
                        <option value="Trừ" ${loaiKhauTru === 'Trừ' ? 'selected' : ''}>Trừ</option>
                    </select>
                </td>
                <td class="p-2 text-center">
                    <input id="so_tien_kt_new_${deductionIndex}" type="number" step="1000" value="${parseFloat(soTienKt).toFixed(2)}" class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-transparent focus:ring-2 focus:ring-blue-500" readonly>
                </td>
                <td class="p-2 text-center">
                    <input id="ly_do_khau_tru_new_${deductionIndex}" type="text" value="${lyDoKhauTru}" class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-transparent focus:ring-2 focus:ring-blue-500" readonly>
                </td>
                <td class="p-2 text-center">
                    <input id="ngay_khau_tru_new_${deductionIndex}" type="date" value="${ngayKhauTru}" class="w-full text-center border border-gray-200 rounded-lg py-1 px-2 text-sm bg-transparent focus:ring-2 focus:ring-blue-500" readonly>
                </td>
                <td class="p-2 text-center flex justify-center gap-1">

                    <a href="javascript:void(0);" class="bg-blue-600 text-white text-xs font-medium px-2 py-1 rounded-lg hover:bg-blue-700 transition duration-300" id="edit-new-${deductionIndex}" onclick="editDiscount('new_${deductionIndex}')" title="Chỉnh sửa">
                        <i class="fa fa-edit"></i>
                    </a>
                    <a href="javascript:void(0);" class="bg-red-600 text-white text-xs font-medium px-2 py-1 rounded-lg hover:bg-red-700 transition duration-300" onclick="deleteDeduction('new_${deductionIndex}')" title="Xóa">
                        <i class="fa fa-trash"></i>
                    </a>
                </td>
            `;
            discountDetails.appendChild(newRow);
            noDeductionMessage.classList.add('hidden');

            // Add hidden inputs
            const inputs = [
                { name: `khautru[${deductionIndex}][NGAYKHAUTRU]`, value: ngayKhauTru },
                { name: `khautru[${deductionIndex}][LOAI_KHAU_TRU]`, value: loaiKhauTru },
                { name: `khautru[${deductionIndex}][SO_TIEN_KT]`, value: soTienKt },
                { name: `khautru[${deductionIndex}][LY_DO_KHAU_TRU]`, value: lyDoKhauTru }
            ];

            inputs.forEach(input => {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = input.name;
                hiddenInput.value = input.value;
                hiddenInput.id = `hidden_${input.name.replace(/[\[\]]/g, '_')}`;
                form.appendChild(hiddenInput);
            });

            deductionIndex++;
        }

        calculateTotalDeduction();
        deductionModal.classList.add('hidden');
        editingDeductionId = null;
    }
});

function editDiscount(id) {
    const row = document.getElementById(`khautru_${id}`);
    if (row) {
        const ngayKhauTru = row.querySelector(`#ngay_khau_tru_${id}`).value;
        const loaiKhauTru = row.querySelector(`#loai_khau_tru_${id}`).value;
        const soTienKt = row.querySelector(`#so_tien_kt_${id}`).value;
        const lyDoKhauTru = row.querySelector(`#ly_do_khau_tru_${id}`).value;

        modalTitle.textContent = 'Chỉnh sửa khấu trừ';
        document.getElementById('modal_NGAYKHAUTRU').value = ngayKhauTru;
        document.getElementById('modal_LOAI_KHAU_TRU').value = loaiKhauTru;
        document.getElementById('modal_SO_TIEN_KT').value = soTienKt;
        document.getElementById('modal_LY_DO_KHAU_TRU').value = lyDoKhauTru;
        document.querySelectorAll('.text-red-500').forEach(el => el.classList.add('hidden'));
        editingDeductionId = id;
        deductionModal.classList.remove('hidden');
    }
}

function deleteDeduction(id) {
    const row = document.getElementById(`khautru_${id}`);
    if (row) {
        row.remove();
        // Remove hidden inputs
        const form = document.getElementById('invoice-form');
        const cleanId = id.replace('new_', '');
        const inputs = form.querySelectorAll(`input[id^="hidden_khautru_${cleanId}_"]`);
        inputs.forEach(input => input.remove());
        
        // Update row numbers
        const rows = discountDetails.children;
        for (let i = 0; i < rows.length; i++) {
            rows[i].children[0].textContent = i + 1;
        }
        
        if (rows.length === 0) {
            noDeductionMessage.classList.remove('hidden');
        }
        calculateTotalDeduction();
    }
}

function calculateTotalDeduction() {
    let totalDeduction = 0;
    const rows = discountDetails.children;
    
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const selectElement = row.querySelector('select');
        const inputElement = row.querySelector('input[type="number"]');
        
        if (selectElement && inputElement) {
            const type = selectElement.value;
            const amount = parseFloat(inputElement.value) || 0;
            totalDeduction += (type === 'Cộng' ? amount : -amount);
        }
    }
    
    document.getElementById('TIEN_KHAU_TRU').value = totalDeduction.toFixed(2);
    
    // Gọi hàm tính tổng hóa đơn từ template chính nếu có
    if (typeof calculateTotals === 'function') {
        calculateTotals();
    } else if (typeof calculateTotalInvoice === 'function') {
        calculateTotalInvoice();
    }
}

function calculateTotalInvoice() {
    const tienPhongElement = document.getElementById('TIEN_PHONG');
    const tienDichVuElement = document.getElementById('TIEN_DICH_VU');
    const tienCocElement = document.getElementById('TIEN_COC');
    const tienKhauTruElement = document.getElementById('TIEN_KHAU_TRU');
    const tongTienElement = document.getElementById('TONG_TIEN');
    
    const tienPhong = parseFloat(tienPhongElement?.value) || 0;
    const tienDichVu = parseFloat(tienDichVuElement?.value) || 0;
    const tienCoc = parseFloat(tienCocElement?.value) || 0;
    const tienKhauTru = parseFloat(tienKhauTruElement?.value) || 0;
    
    const tongTien = tienPhong + tienDichVu + tienCoc + tienKhauTru;
    
    if (tongTienElement) {
        tongTienElement.value = tongTien.toFixed(2);
    }
    
    // Cập nhật display trong footer nếu có
    const totalAmountDisplay = document.getElementById('total_amount_display');
    if (totalAmountDisplay) {
        totalAmountDisplay.textContent = `Tổng tiền: ${tongTien.toLocaleString('vi-VN')} VNĐ`;
    }
}

// Thêm event listeners khi DOM loaded
document.addEventListener('DOMContentLoaded', function() {
    ['TIEN_PHONG', 'TIEN_DICH_VU', 'TIEN_COC'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', calculateTotalInvoice);
        }
    });
});

