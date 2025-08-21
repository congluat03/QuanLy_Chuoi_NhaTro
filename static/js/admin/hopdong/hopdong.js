function toggleMenuHopDong(khachThueId) {
    const menu = document.getElementById("menuHopDong-" + khachThueId);

    // Ẩn tất cả các menu khác
    const allMenus = document.querySelectorAll("[id^='menuHopDong-']");
    allMenus.forEach((m) => {
        if (!m.classList.contains("hidden")) {
            m.classList.add("hidden");
            // Đồng thời bỏ luôn sự kiện mouseleave cũ để tránh bị dính nhiều lần
            m.onmouseleave = null;
        }
    });

    // Nếu menu đang hiển thị => ẩn
    if (!menu.classList.contains("hidden")) {
        menu.classList.add("hidden");
        menu.onmouseleave = null;
        return;
    }

    // Xử lý vị trí nếu bị tràn màn hình
    menu.classList.remove("top-8");
    menu.classList.remove("bottom-full");

    // Reset lại vị trí để đo đúng
    menu.style.top = "";
    menu.style.bottom = "";

    // Tạm thời hiển thị để đo vị trí
    menu.classList.remove("hidden");

    const rect = menu.getBoundingClientRect();
    const windowHeight = window.innerHeight;

    // Nếu bị tràn dưới thì hiển thị menu lên trên
    if (rect.bottom > windowHeight) {
        menu.classList.add("bottom-full");
        menu.classList.remove("top-8");
    } else {
        menu.classList.add("top-8");
        menu.classList.remove("bottom-full");
    }

    // Hiển thị menu
    menu.classList.remove("hidden");

    // Thêm sự kiện khi chuột rời khỏi menu thì ẩn menu
    menu.onmouseleave = () => {
        menu.classList.add("hidden");
        menu.onmouseleave = null; // gỡ sự kiện sau khi ẩn menu
    };
}

function showChucNangHopDong(type, khachThueId) {
    let url = "";
    let initFunction = null;

    switch (type) {
        case "chitiet":
            url = "/hopdong/viewChiTietHopDong/" + khachThueId;
            initFunction = initThongTin;
            break;
        case "chinhsua":
            url = "/hopdong/viewSuaHopDong/" + khachThueId;
            initFunction = initChiSua;
            break;
        case "themThanhVien":
            url = "/hopdong/viewThemThanhVien/" + khachThueId;
            initFunction = initThemThanhVien;
            break;
        default:
            console.log("Invalid type");
            return;
    }

    // Giao diện loading Tailwind
    document.getElementById("modalContentHopDong").innerHTML = `
        <div class="text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-700 mx-auto mb-4"></div>
            <p class="text-blue-700">Đang tải nội dung hợp đồng...</p>
        </div>
    `;

    // Hiển thị modal (bỏ class hidden)
    document.getElementById("hopDongModal").classList.remove("hidden");

    // Load nội dung
    fetch(url)
        .then((response) => {
            if (!response.ok) {
                throw new Error("HTTP error " + response.status);
            }
            return response.text();
        })
        .then((data) => {
            document.getElementById("modalContentHopDong").innerHTML = data;
            if (initFunction) initFunction();
        })
        .catch((error) => {
            console.error("Error loading modal content:", error);
            document.getElementById("modalContentHopDong").innerHTML = `
                <div class="text-red-600 text-center p-4 bg-red-100 rounded-lg">
                    Không thể tải nội dung. Vui lòng thử lại sau.
                </div>
            `;
        });
}
function toggleHopDongModal(show = true) {
    const modal = document.getElementById("hopDongModal");
    if (show) {
        modal.classList.remove("hidden");
    } else {
        modal.classList.add("hidden");
    }
}

function XoaHopDong(dichVuId) {
    // Kiểm tra ID dịch vụ hợp lệ
    if (!dichVuId) {
        alert("ID dịch vụ không hợp lệ.");
        return;
    }
    // Xác nhận xóa
    if (confirm("Bạn có chắc chắn muốn xóa hợp đồng này?")) {
        // Gửi yêu cầu xóa dịch vụ
        fetch(`/hopdong/xoaHopDong/${dichVuId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Nếu xóa thành công, thông báo và đóng modal
                    alert(data.message); // Thông báo thành công             
                    // Tải lại trang để cập nhật danh sách
                    location.reload();
                } else {
                    // Nếu có lỗi khi xóa, thông báo lỗi
                    alert(data.message); // Thông báo lỗi
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Có lỗi xảy ra, vui lòng thử lại!');
            });
    } else {
        // Nếu không xác nhận xóa
        return;
    }
}
function huyHopDong(dichVuId) {
    // Kiểm tra ID hợp đồng hợp lệ
    if (!dichVuId) {
        alert("ID hợp đồng không hợp lệ.");
        return;
    }

    // Lấy ngày hiện tại theo định dạng MySQL (YYYY-MM-DD)
    const currentDate = new Date().toISOString().split('T')[0];

    // Xác nhận hủy hợp đồng
    if (confirm("Bạn có chắc chắn muốn hủy hợp đồng này?")) {
        // Gửi yêu cầu hủy hợp đồng
        fetch(`/hopdong/huyHopDong/${dichVuId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                NGAYKETTHUCHD: currentDate // Đổi tên tham số thành NGAYKETTHUCHD cho khớp với controller
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Nếu hủy hợp đồng thành công, thông báo và cập nhật trạng thái
                    alert(data.message); // Thông báo thành công

                    // Cập nhật trạng thái hủy hợp đồng trên bảng
                    location.reload();  // Tải lại trang hoặc cập nhật giao diện theo nhu cầu
                } else {
                    // Nếu có lỗi khi hủy, thông báo lỗi
                    alert(data.message); // Thông báo lỗi
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Có lỗi xảy ra, vui lòng thử lại!' + error);
            });
    } else {
        // Nếu không xác nhận hủy hợp đồng
        return;
    }
}
function KhachHangRoiDi(dichVuId) {
    // Kiểm tra ID hợp đồng hợp lệ
    if (!dichVuId) {
        alert("ID hợp đồng không hợp lệ.");
        return;
    }

    // Lấy ngày hiện tại theo định dạng MySQL (YYYY-MM-DD)
    const currentDate = new Date().toISOString().split('T')[0];
    // Xác nhận rời đi
    if (confirm("Bạn có chắc chắn muốn cập nhật ngày rời đi cho hợp đồng này?")) {
        // Gửi yêu cầu cập nhật ngày rời đi
        fetch(`/hopdong/hopdongkhachthue/trangThaiKhachThue/${dichVuId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            },
            body: JSON.stringify({
                NGAYROI: currentDate // Đổi tên tham số thành NGAYROI cho khớp với controller
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Nếu cập nhật thành công, thông báo và cập nhật trực tiếp trên bảng
                    alert(data.message); // Thông báo thành công

                    // Cập nhật trực tiếp ô ngày rời đi trên bảng
                    const row = document.getElementById(`khachthue-${dichVuId}`);
                    const ngayRoiDiCell = row.querySelector('td:nth-child(5)');
                    ngayRoiDiCell.textContent = currentDate; // Cập nhật ô ngày rời đi

                } else {
                    // Nếu có lỗi khi cập nhật, thông báo lỗi
                    alert(data.message); // Thông báo lỗi
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Có lỗi xảy ra, vui lòng thử lại!' + error);
            });
    } else {
        // Nếu không xác nhận
        return;
    }
}

function initChiSua() {
    const ngayNhanPhongInput = document.getElementById('NGAYNHANPHONG');
    const ngayTraPhongInput = document.getElementById('NGAYTRAPHONG');
    const thoiHanHopDongSelect = document.getElementById('THOIHANHOPDONG');

    // Gắn sự kiện khi thay đổi giá trị
    ngayNhanPhongInput.addEventListener('change', calculateNgayTraPhong);
    thoiHanHopDongSelect.addEventListener('change', calculateNgayTraPhong);
}
// Hàm tính ngày trả phòng
function calculateNgayTraPhong() {
    const ngayNhanPhongInput = document.getElementById('NGAYNHANPHONG');
    const ngayTraPhongInput = document.getElementById('NGAYTRAPHONG');
    const thoiHanHopDongSelect = document.getElementById('THOIHANHOPDONG');
    const ngayNhanPhongValue = ngayNhanPhongInput.value;
    const thoiHanValue = thoiHanHopDongSelect.value;

    if (!ngayNhanPhongValue || !thoiHanValue) {
        ngayTraPhongInput.value = '';
        return;
    }

    const ngayNhanPhong = new Date(ngayNhanPhongValue);

    if (!isNaN(ngayNhanPhong)) {
        let monthsToAdd = 1; // Mặc định là 1 tháng
        const match = thoiHanValue.match(/(\d+)/);

        if (match) {
            monthsToAdd = parseInt(match[1], 10);
            if (thoiHanValue.includes('năm')) {
                monthsToAdd *= 12; // Chuyển đổi năm sang tháng
            }
        }

        ngayNhanPhong.setMonth(ngayNhanPhong.getMonth() + monthsToAdd);
        // Kiểm tra trường hợp ngày bị vượt quá ngày cuối tháng
        if (ngayNhanPhong.getDate() !== parseInt(ngayNhanPhongValue.split('-')[2])) {
            ngayNhanPhong.setDate(0); // Lùi về cuối tháng trước
        }

        ngayTraPhongInput.value = ngayNhanPhong.toISOString().split('T')[0];
    } else {
        ngayTraPhongInput.value = '';
    }
}
function toggleElementsDisplay(elementIds) {
    elementIds.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.style.display = (element.style.display === "none" || element.style.display === "") 
                ? "block" 
                : "none";
        }
    });
}

function initThongTin() {
}

// ======================= FUNCTIONS CHO HÓA ĐƠN BẮT ĐẦU HỢP ĐỒNG =======================

/**
 * Hiển thị modal hóa đơn bắt đầu hợp đồng
 * @param {Object} invoiceData - Dữ liệu hóa đơn từ server
 */
function showHoaDonModal(invoiceData) {
    console.log('🧾 Hiển thị hóa đơn:', invoiceData);
    
    // Lấy template và clone
    const template = document.getElementById('hoadon-template');
    const modal = document.getElementById('hoadon-modal');
    const content = document.getElementById('hoadon-content');
    
    if (!template || !modal || !content) {
        console.error('❌ Không tìm thấy template hoặc modal hóa đơn');
        return;
    }
    
    // Clone template content
    const templateContent = template.content.cloneNode(true);
    
    // Điền dữ liệu vào template
    fillInvoiceTemplate(templateContent, invoiceData);
    
    // Thay thế nội dung modal
    content.innerHTML = '';
    content.appendChild(templateContent);
    
    // Hiển thị modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Ngăn scroll body
}

/**
 * Điền dữ liệu vào template hóa đơn
 * @param {DocumentFragment} template - Template đã clone
 * @param {Object} data - Dữ liệu hóa đơn
 */
function fillInvoiceTemplate(template, data) {
    const mappings = {
        '.hd-ma-hoa-don': data.ma_hoa_don,
        '.hd-ngay-lap': data.ngay_lap,
        '.hd-loai': data.loai_hoa_don,
        '.hd-ma-hop-dong': data.ma_hop_dong,
        '.hd-ten-phong': data.ten_phong,
        '.hd-ngay-nhan-phong': data.ngay_nhan_phong,
        '.hd-ngay-tra-phong': data.ngay_tra_phong,
        '.hd-ten-khach-thue': data.ten_khach_thue,
        '.hd-sdt-khach-thue': data.sdt_khach_thue,
        '.hd-ngay-sinh': data.ngay_sinh,
        '.hd-tien-phong': data.tien_phong,
        '.hd-tien-dich-vu': data.tien_dich_vu,
        '.hd-tien-coc': data.tien_coc,
        '.hd-tien-khau-tru': data.tien_khau_tru,
        '.hd-tong-tien': data.tong_tien,
        '.hd-trang-thai': data.trang_thai,
        '.hd-han-thanh-toan': data.han_thanh_toan,
        '.hd-ngay-tao': data.ngay_tao
    };
    
    // Điền dữ liệu cho từng element
    Object.entries(mappings).forEach(([selector, value]) => {
        const elements = template.querySelectorAll(selector);
        elements.forEach(el => {
            if (el) {
                el.textContent = value || '-';
            }
        });
    });
}

/**
 * Đóng modal hóa đơn
 */
function closeHoaDonModal() {
    const modal = document.getElementById('hoadon-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = ''; // Khôi phục scroll body
    }
}

/**
 * In hóa đơn
 */
function printHoaDon() {
    console.log('🖨️ In hóa đơn');
    
    // Ẩn các element không cần in
    const noprint = document.querySelectorAll('.no-print');
    noprint.forEach(el => el.style.display = 'none');
    
    // In
    window.print();
    
    // Khôi phục hiển thị
    noprint.forEach(el => el.style.display = '');
}

/**
 * Tải hóa đơn dưới dạng PDF
 */
function downloadHoaDonPDF() {
    console.log('📄 Tải PDF hóa đơn');
    
    // Lấy mã hóa đơn từ template
    const ma_hoa_don = document.querySelector('.hd-ma-hoa-don')?.textContent;
    if (!ma_hoa_don) {
        showNotification('Không tìm thấy mã hóa đơn', 'error');
        return;
    }
    
    // Gọi API backend để tạo và tải PDF
    const downloadUrl = `/admin/hopdong/api/export-invoice-pdf/${ma_hoa_don}/`;
    
    // Tạo link ẩn để tải file
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `hoadon_${ma_hoa_don}.pdf`;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showNotification('Đang tải PDF hóa đơn...', 'info');
}

/**
 * Chia sẻ hóa đơn
 */
function shareHoaDon() {
    console.log('📤 Chia sẻ hóa đơn');
    
    const ma_hoa_don = document.querySelector('.hd-ma-hoa-don')?.textContent;
    if (!ma_hoa_don) {
        showNotification('Không tìm thấy mã hóa đơn', 'error');
        return;
    }
    
    // Hiển thị modal chia sẻ với các tùy chọn
    showShareModal(ma_hoa_don);
}

/**
 * Hiển thị modal chia sẻ với các tùy chọn
 */
function showShareModal(ma_hoa_don) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div class="flex justify-between items-center p-4 border-b border-gray-200">
                <h3 class="text-lg font-semibold text-gray-900">Chia sẻ hóa đơn #${ma_hoa_don}</h3>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-400 hover:text-gray-600">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">Email người nhận</label>
                    <input type="email" id="shareEmail" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" placeholder="Nhập email...">
                </div>
                <div class="flex space-x-3">
                    <button onclick="sendInvoiceEmail('${ma_hoa_don}')" class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition">
                        <i class="fas fa-envelope mr-2"></i>
                        Gửi Email
                    </button>
                    <button onclick="copyInvoiceLink('${ma_hoa_don}')" class="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition">
                        <i class="fas fa-link mr-2"></i>
                        Copy Link
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Focus vào input email
    setTimeout(() => {
        const emailInput = modal.querySelector('#shareEmail');
        if (emailInput) emailInput.focus();
    }, 100);
}

/**
 * Gửi hóa đơn qua email
 */
function sendInvoiceEmail(ma_hoa_don) {
    const emailInput = document.getElementById('shareEmail');
    const email = emailInput?.value?.trim();
    
    if (!email) {
        showNotification('Vui lòng nhập email người nhận', 'error');
        return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showNotification('Email không hợp lệ', 'error');
        return;
    }
    
    // Gửi request tới API
    fetch(`/admin/hopdong/api/send-invoice-email/${ma_hoa_don}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        },
        body: JSON.stringify({ email: email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            // Đóng modal
            document.querySelector('.fixed.inset-0')?.remove();
        } else {
            showNotification(data.message || 'Lỗi gửi email', 'error');
        }
    })
    .catch(error => {
        console.error('❌ Lỗi gửi email:', error);
        showNotification('Lỗi kết nối', 'error');
    });
}

/**
 * Copy link hóa đơn
 */
function copyInvoiceLink(ma_hoa_don) {
    const link = `${window.location.origin}/admin/hopdong/api/export-invoice-pdf/${ma_hoa_don}/`;
    
    navigator.clipboard.writeText(link)
        .then(() => {
            showNotification('Đã copy link hóa đơn!', 'success');
            // Đóng modal
            document.querySelector('.fixed.inset-0')?.remove();
        })
        .catch(() => {
            showNotification('Không thể copy link', 'error');
        });
}

/**
 * Utility function: Lấy timestamp hiện tại
 */
function getCurrentTimestamp() {
    return new Date().toISOString().slice(0, 19).replace(/:/g, '-');
}

/**
 * Utility function: Hiển thị notification
 */
function showNotification(message, type = 'info') {
    // Tạo notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg text-white transition-all duration-300 ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-blue-500'
    }`;
    notification.textContent = message;
    
    // Thêm vào DOM
    document.body.appendChild(notification);
    
    // Auto remove sau 3s
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// ======================= CẬP NHẬT WORKFLOW ACTION =======================

/**
 * Override workflow action handler để xử lý hiển thị hóa đơn
 */
if (typeof executeWorkflowAction === 'function') {
    const originalExecuteWorkflowAction = executeWorkflowAction;
    
    executeWorkflowAction = function(action, contractId, additionalData = {}) {
        console.log(`🔄 Executing workflow action: ${action} for contract ${contractId}`);
        
        // Gọi function gốc và xử lý response
        const result = originalExecuteWorkflowAction(action, contractId, additionalData);
        
        // Nếu là Promise, handle response
        if (result && typeof result.then === 'function') {
            return result.then(response => {
                if (response && response.show_invoice && response.invoice_data) {
                    console.log('🧾 Response có hóa đơn, hiển thị modal');
                    setTimeout(() => showHoaDonModal(response.invoice_data), 500);
                }
                return response;
            });
        }
        
        return result;
    };
} else {
    console.warn('⚠️ Function executeWorkflowAction không tồn tại, tạo mới');
    
    // Tạo function mới nếu chưa có
    window.executeWorkflowAction = function(action, contractId, additionalData = {}) {
        console.log(`🔄 Executing workflow action: ${action} for contract ${contractId}`);
        
        const data = {
            action: action,
            ma_hop_dong: contractId,
            ...additionalData
        };
        
        return fetch('/admin/hopdong/workflow-action/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            console.log('📦 Workflow response:', data);
            
            if (data.success) {
                showNotification(data.message, 'success');
                
                // Hiển thị modal hóa đơn nếu có
                if (data.show_invoice && data.invoice_data) {
                    setTimeout(() => showHoaDonModal(data.invoice_data), 500);
                }
                
                // Reload trang sau 2s để cập nhật UI
                setTimeout(() => window.location.reload(), 2000);
            } else {
                showNotification(data.message || 'Có lỗi xảy ra', 'error');
            }
            
            return data;
        })
        .catch(error => {
            console.error('❌ Workflow error:', error);
            showNotification('Lỗi kết nối', 'error');
            throw error;
        });
    };
}

