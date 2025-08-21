/**
 * JavaScript cho chức năng thiết lập hóa đơn bắt đầu hợp đồng
 */

class TaoHoaDonBatDau {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCSRFToken();
    }

    /**
     * Đóng modal tạo hóa đơn
     */
    closeTaoHoaDonModal() {
        const modal = $('#modalTaoHoaDonBatDau');
        modal.addClass('hidden');
        modal.removeClass('flex');
        setTimeout(() => modal.remove(), 300);
    }

    /**
     * Đóng modal xem hóa đơn
     */
    closeXemHoaDonModal() {
        const modal = $('#modalXemHoaDon');
        modal.addClass('hidden');
        modal.removeClass('flex');
        setTimeout(() => modal.remove(), 300);
    }

    bindEvents() {
        // Mở modal tạo hóa đơn
        $(document).on('click', '.btn-tao-hoa-don', (e) => {
            e.preventDefault();
            const maHopDong = $(e.currentTarget).data('ma-hop-dong');
            this.openTaoHoaDonModal(maHopDong);
        });

        // Xem hóa đơn hiện tại
        $(document).on('click', '.btn-xem-hoa-don', (e) => {
            e.preventDefault();
            const maHopDong = $(e.currentTarget).data('ma-hop-dong');
            this.xemHoaDonHienTai(maHopDong);
        });

        // Xóa hóa đơn
        $(document).on('click', '.btn-xoa-hoa-don', (e) => {
            e.preventDefault();
            const maHopDong = $(e.currentTarget).data('ma-hop-dong');
            this.xoaHoaDon(maHopDong);
        });
    }

    loadCSRFToken() {
        this.csrfToken = $('[name=csrfmiddlewaretoken]').val() || 
                        $('meta[name=csrf-token]').attr('content');
    }

    /**
     * Mở modal tạo hóa đơn bắt đầu
     */
    openTaoHoaDonModal(maHopDong) {
        this.showLoading('Đang tải cấu hình...');
        
        $.ajax({
            url: `/admin/hopdong/thiet-lap-hoa-don-bat-dau/${maHopDong}/`,
            method: 'GET',
            success: (response) => {
                this.hideLoading();
                if (response.success) {
                    this.showTaoHoaDonModal(response.html);
                } else {
                    this.showError(response.message);
                }
            },
            error: (xhr) => {
                this.hideLoading();
                this.handleAjaxError(xhr);
            }
        });
    }

    /**
     * Hiển thị modal tạo hóa đơn với HTML được trả về
     */
    showTaoHoaDonModal(html) {
        // Xóa modal cũ nếu có
        $('#modalTaoHoaDonBatDau').remove();
        
        // Thêm HTML vào body
        $('body').append(html);
        
        // Hiển thị modal bằng Tailwind classes
        const modal = $('#modalTaoHoaDonBatDau');
        modal.removeClass('hidden');
        modal.addClass('flex');
        
        // Bind events cho modal mới
        this.bindModalEvents();
        
        // Bind close events
        modal.find('[data-modal-close]').on('click', () => {
            this.closeTaoHoaDonModal();
        });
        
        // Close on backdrop click
        modal.on('click', (e) => {
            if (e.target === modal[0]) {
                this.closeTaoHoaDonModal();
            }
        });
    }

    /**
     * Bind events cho modal
     */
    bindModalEvents() {
        const modal = $('#modalThietLapHoaDonBatDau');

        // Xử lý chọn cấu hình
        modal.on('change', '.cau-hinh-radio', (e) => {
            this.handleConfigSelection(e);
        });

        // Xử lý click card để chọn radio
        modal.on('click', '.cau-hinh-card', (e) => {
            if (!$(e.target).hasClass('form-check-input') && 
                !$(e.target).hasClass('allow-custom-checkbox') &&
                !$(e.target).hasClass('custom-value-input')) {
                $(e.currentTarget).find('.cau-hinh-radio').trigger('click');
            }
        });

        // Xử lý checkbox cho phép tùy chỉnh
        modal.on('change', '.allow-custom-checkbox', (e) => {
            this.handleCustomValueToggle(e);
        });

        // Xử lý thay đổi giá trị tùy chỉnh
        modal.on('input', '.custom-value-input', (e) => {
            this.handleCustomValueChange(e);
        });

        // Xử lý lưu thiết lập
        modal.on('click', '#btnLuuThietLap', () => {
            this.luuThietLap();
        });

        // Auto select cấu hình mặc định
        modal.find('.cau-hinh-radio:checked').trigger('change');
    }

    /**
     * Xử lý khi chọn cấu hình
     */
    handleConfigSelection(e) {
        const selectedCard = $(e.target).closest('.cau-hinh-card');
        const configId = $(e.target).val();

        // Cập nhật UI
        $('.cau-hinh-card').removeClass('selected');
        selectedCard.addClass('selected');
        
        // Reset tất cả inputs
        $('.custom-value-input').prop('disabled', true).removeClass('bg-warning');
        $('.allow-custom-checkbox').prop('checked', false);
        
        // Enable inputs cho cấu hình được chọn
        $(`.custom-value-input[data-config-id="${configId}"]`).prop('disabled', false);
    }

    /**
     * Xử lý toggle checkbox tùy chỉnh
     */
    handleCustomValueToggle(e) {
        const configId = $(e.target).data('config-id');
        const inputs = $(`.custom-value-input[data-config-id="${configId}"]`);
        
        if ($(e.target).is(':checked')) {
            inputs.prop('readonly', false).addClass('bg-warning');
        } else {
            inputs.prop('readonly', true).removeClass('bg-warning');
            // Reset về giá trị gốc
            inputs.each(function() {
                const originalValue = $(this).data('original-value') || $(this).val();
                $(this).val(originalValue);
            });
        }
        
        this.updateConfigTotal(configId);
    }

    /**
     * Xử lý thay đổi giá trị tùy chỉnh
     */
    handleCustomValueChange(e) {
        const configId = $(e.target).data('config-id');
        this.updateConfigTotal(configId);
    }

    /**
     * Cập nhật tổng tiền cho cấu hình
     */
    updateConfigTotal(configId) {
        let total = 0;
        $(`.custom-value-input[data-config-id="${configId}"]`).each(function() {
            const value = parseFloat($(this).val()) || 0;
            total += value;
            
            // Cập nhật thành tiền
            $(this).closest('tr').find('.thanh-tien').text(
                value.toLocaleString('vi-VN')
            );
        });
        
        // Cập nhật tổng cộng
        $(`.cau-hinh-card[data-cau-hinh-id="${configId}"] .config-total`).text(
            total.toLocaleString('vi-VN')
        );
    }

    /**
     * Lưu thiết lập
     */
    luuThietLap() {
        const maHopDong = $('[name="ma_hop_dong"]').val();

        // Hiển thị loading
        this.showButtonLoading('#btnLuuThietLap', 'Đang tạo...');

        // Gửi request đơn giản
        $.ajax({
            url: `/admin/hopdong/thiet-lap-hoa-don-bat-dau/${maHopDong}/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken,
                'Content-Type': 'application/json'
            },
            data: JSON.stringify({}), // POST request đơn giản, không cần cấu hình
            success: (response) => {
                this.hideButtonLoading('#btnLuuThietLap', 'Tạo hóa đơn');
                
                if (response.success) {
                    this.showSuccess(response.message);
                    this.closeTaoHoaDonModal();
                    
                    // Refresh trang để cập nhật UI
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    this.showError(response.message);
                }
            },
            error: (xhr) => {
                this.hideButtonLoading('#btnLuuThietLap', 'Tạo hóa đơn');
                this.handleAjaxError(xhr);
            }
        });
    }

    /**
     * Xem hóa đơn hiện tại
     */
    xemHoaDonHienTai(maHopDong) {
        this.showLoading('Đang tải thông tin hóa đơn...');
        
        $.ajax({
            url: `/admin/hopdong/xem-hoa-don-bat-dau/${maHopDong}/`,
            method: 'GET',
            success: (response) => {
                this.hideLoading();
                
                if (response.success) {
                    this.showHoaDonDetail(response.data);
                } else {
                    this.showError(response.message);
                }
            },
            error: (xhr) => {
                this.hideLoading();
                this.handleAjaxError(xhr);
            }
        });
    }

    /**
     * Hiển thị chi tiết hóa đơn
     */
    showHoaDonDetail(data) {
        let html = `
            <div class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden" id="modalXemHoaDon">
                <div class="flex items-center justify-center min-h-screen p-4">
                    <div class="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
                        <div class="bg-blue-600 text-white p-6 rounded-t-xl">
                            <div class="flex items-center justify-between">
                                <h5 class="text-xl font-semibold flex items-center">
                                    <i class="fas fa-eye mr-3"></i>
                                    Chi tiết Hóa đơn bắt đầu #${data.ma_hoa_don}
                                </h5>
                                <button type="button" class="text-white hover:text-gray-200 transition" data-modal-close>
                                    <i class="fas fa-times text-xl"></i>
                                </button>
                            </div>
                        </div>
                        <div class="p-6">
                            <div class="grid md:grid-cols-2 gap-6 mb-6">
                                <div class="bg-gray-50 p-4 rounded-lg">
                                    <h6 class="font-semibold text-gray-800 mb-3">Thông tin hợp đồng</h6>
                                    <div class="space-y-2 text-sm">
                                        <p><span class="font-medium text-gray-600">Mã hợp đồng:</span> <span class="font-mono">${data.ma_hop_dong}</span></p>
                                        <p><span class="font-medium text-gray-600">Phòng:</span> ${data.ten_phong}</p>
                                        <p><span class="font-medium text-gray-600">Khách thuê:</span> ${data.ten_khach_thue}</p>
                                    </div>
                                </div>
                                <div class="bg-gray-50 p-4 rounded-lg">
                                    <h6 class="font-semibold text-gray-800 mb-3">Chi tiết hóa đơn</h6>
                                    <div class="space-y-2 text-sm">
                                        <p><span class="font-medium text-gray-600">Ngày lập:</span> ${data.ngay_lap}</p>
                                        <p><span class="font-medium text-gray-600">Loại hóa đơn:</span> ${data.loai_hoa_don}</p>
                                        <p><span class="font-medium text-gray-600">Trạng thái:</span> 
                                            <span class="px-2 py-1 rounded-full text-xs font-medium ${data.trang_thai === 'Đã thanh toán' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">${data.trang_thai}</span>
                                        </p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
                                <div class="bg-gray-50 px-4 py-3">
                                    <h6 class="font-semibold text-gray-800">Chi tiết thanh toán</h6>
                                </div>
                                <div class="overflow-x-auto">
                                    <table class="w-full">
                                        <thead class="bg-gray-100">
                                            <tr>
                                                <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700">Khoản phí</th>
                                                <th class="px-4 py-3 text-right text-sm font-semibold text-gray-700">Số tiền</th>
                                            </tr>
                                        </thead>
                                        <tbody class="divide-y divide-gray-200">
                                            <tr class="hover:bg-gray-50">
                                                <td class="px-4 py-3 text-sm text-gray-900">
                                                    <i class="fas fa-home mr-2 text-blue-600"></i>Tiền phòng
                                                </td>
                                                <td class="px-4 py-3 text-sm text-gray-900 text-right font-mono">${data.tien_phong} VNĐ</td>
                                            </tr>
                                            <tr class="hover:bg-gray-50">
                                                <td class="px-4 py-3 text-sm text-gray-900">
                                                    <i class="fas fa-tools mr-2 text-green-600"></i>Tiền dịch vụ
                                                </td>
                                                <td class="px-4 py-3 text-sm text-gray-900 text-right font-mono">${data.tien_dich_vu} VNĐ</td>
                                            </tr>
                                            <tr class="hover:bg-gray-50">
                                                <td class="px-4 py-3 text-sm text-gray-900">
                                                    <i class="fas fa-shield-alt mr-2 text-yellow-600"></i>Tiền cọc
                                                </td>
                                                <td class="px-4 py-3 text-sm text-gray-900 text-right font-mono">${data.tien_coc} VNĐ</td>
                                            </tr>
                                            <tr class="hover:bg-gray-50">
                                                <td class="px-4 py-3 text-sm text-gray-900">
                                                    <i class="fas fa-minus-circle mr-2 text-red-600"></i>Tiền khấu trừ
                                                </td>
                                                <td class="px-4 py-3 text-sm text-gray-900 text-right font-mono">${data.tien_khau_tru} VNĐ</td>
                                            </tr>
                                        </tbody>
                                        <tfoot class="bg-blue-50">
                                            <tr>
                                                <th class="px-4 py-4 text-base font-bold text-blue-800">
                                                    <i class="fas fa-calculator mr-2"></i>Tổng cộng:
                                                </th>
                                                <th class="px-4 py-4 text-base font-bold text-blue-800 text-right font-mono">${data.tong_tien} VNĐ</th>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            </div>
                        </div>
                        <div class="flex flex-wrap justify-end gap-3 p-6 bg-gray-50 rounded-b-xl border-t">
                            <button type="button" class="bg-gray-500 text-white px-4 py-2 rounded-md hover:bg-gray-600 transition" data-modal-close>Đóng</button>
                            ${data.can_delete ? `
                                <button type="button" class="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition" onclick="instance.xoaHoaDon('${data.ma_hop_dong}'); instance.closeXemHoaDonModal();">
                                    <i class="fas fa-trash mr-2"></i>Xóa hóa đơn
                                </button>
                            ` : ''}
                            <button type="button" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition" onclick="window.print()">
                                <i class="fas fa-print mr-2"></i>In hóa đơn
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal and show new one
        $('#modalXemHoaDon').remove();
        $('body').append(html);
        
        const modal = $('#modalXemHoaDon');
        modal.removeClass('hidden');
        modal.addClass('flex');
        
        // Bind close events
        modal.find('[data-modal-close]').on('click', () => {
            this.closeXemHoaDonModal();
        });
        
        // Close on backdrop click
        modal.on('click', (e) => {
            if (e.target === modal[0]) {
                this.closeXemHoaDonModal();
            }
        });
        
        // Set instance reference for callback
        window.instance = this;
    }

    /**
     * Xóa hóa đơn bắt đầu
     */
    xoaHoaDon(maHopDong) {
        if (!confirm('Bạn có chắc chắn muốn xóa hóa đơn bắt đầu của hợp đồng này? Hóa đơn đã thanh toán sẽ không thể xóa.')) {
            return;
        }

        this.showLoading('Đang xóa hóa đơn...');

        $.ajax({
            url: `/admin/hopdong/xoa-hoa-don-bat-dau/${maHopDong}/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': this.csrfToken
            },
            success: (response) => {
                this.hideLoading();
                
                if (response.success) {
                    this.showSuccess(response.message);
                    this.updateRowStatus(maHopDong, 'Chưa có HĐ bắt đầu');
                } else {
                    this.showError(response.message);
                }
            },
            error: (xhr) => {
                this.hideLoading();
                this.handleAjaxError(xhr);
            }
        });
    }

    /**
     * Cập nhật trạng thái row
     */
    updateRowStatus(maHopDong, status) {
        const row = $(`[data-hop-dong-id="${maHopDong}"]`).closest('tr');
        if (row.length) {
            const actionCell = row.find('.invoice-setup-actions');
            const statusSpan = actionCell.find('.invoice-setup-status');
            
            if (status.includes('Đã có HĐ')) {
                // Đã có hóa đơn - hiển thị icon check và buttons xem/xóa
                statusSpan.html('<i class="fas fa-check-circle mr-1"></i>' + status);
                statusSpan.removeClass('text-gray-500').addClass('text-green-600');
                
                actionCell.find('.btn-tao-hoa-don').hide();
                actionCell.find('.btn-xem-hoa-don, .btn-xoa-hoa-don').show();
                
                // Thêm ngày nếu có
                const currentDate = new Date().toLocaleDateString('en-GB').replace(/\//g, '/');
                const dateDiv = actionCell.find('.text-xs.text-gray-500.mb-1');
                if (dateDiv.length === 0) {
                    statusSpan.after(`<div class="text-xs text-gray-500 mb-1">${currentDate}</div>`);
                }
                
            } else {
                // Chưa có hóa đơn - hiển thị icon plus và button tạo
                statusSpan.html('<i class="fas fa-plus-circle mr-1"></i>' + status);
                statusSpan.removeClass('text-green-600').addClass('text-gray-500');
                
                actionCell.find('.btn-tao-hoa-don').show();
                actionCell.find('.btn-xem-hoa-don, .btn-xoa-hoa-don').hide();
                
                // Xóa ngày nếu có
                actionCell.find('.text-xs.text-gray-500.mb-1').remove();
            }
        }
    }

    /**
     * Utility methods
     */
    showLoading(message = 'Đang xử lý...') {
        if ($('#globalLoading').length === 0) {
            $('body').append(`
                <div id="globalLoading" class="position-fixed top-50 start-50 translate-middle" 
                     style="z-index: 9999; background: rgba(255,255,255,0.9); padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <div class="d-flex align-items-center">
                        <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                        <span>${message}</span>
                    </div>
                </div>
            `);
        }
    }

    hideLoading() {
        $('#globalLoading').remove();
    }

    showButtonLoading(selector, loadingText) {
        const btn = $(selector);
        btn.data('original-text', btn.html());
        btn.html(`
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${loadingText}
        `).prop('disabled', true);
    }

    hideButtonLoading(selector, originalText) {
        const btn = $(selector);
        const original = btn.data('original-text') || originalText;
        btn.html(original).prop('disabled', false);
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'error');
    }

    showToast(message, type = 'info') {
        const bgClass = type === 'success' ? 'bg-green-600' : 
                       type === 'error' ? 'bg-red-600' : 'bg-blue-600';
        
        const toast = $(`
            <div class="fixed top-4 right-4 ${bgClass} text-white px-6 py-4 rounded-lg shadow-lg z-50 transform translate-x-full opacity-0 transition-all duration-300 ease-in-out" 
                 role="alert" aria-live="assertive" aria-atomic="true">
                <div class="flex items-center justify-between">
                    <div class="flex items-center">
                        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} mr-3"></i>
                        <span>${message}</span>
                    </div>
                    <button type="button" class="ml-4 text-white hover:text-gray-200 transition" onclick="$(this).parent().parent().remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `);
        
        $('body').append(toast);
        
        // Animate in
        setTimeout(() => {
            toast.removeClass('translate-x-full opacity-0');
            toast.addClass('translate-x-0 opacity-100');
        }, 100);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.addClass('translate-x-full opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    handleAjaxError(xhr) {
        let message = 'Có lỗi xảy ra!';
        
        if (xhr.responseJSON && xhr.responseJSON.message) {
            message = xhr.responseJSON.message;
        } else if (xhr.statusText) {
            message = `Lỗi ${xhr.status}: ${xhr.statusText}`;
        }
        
        this.showError(message);
    }
}

// Khởi tạo khi document ready
$(document).ready(function() {
    new TaoHoaDonBatDau();
});