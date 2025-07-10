
document.addEventListener("DOMContentLoaded", function () {
    // Gọi API mặc định với tất cả khu vực và tháng hiện tại
    fetchThongKeDichVu();
});
// Đóng modal khi nhấn ESC
document.addEventListener('keydown', (e) => {
    const modal = document.getElementById('addServiceModal');
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
        toggleModal(false);
    }
});
function toggleServiceModal(show) {
    const modal = document.getElementById('serviceModal');
    if (show) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

async function showModalDichVu(type, dichVuId = null) {
    const modal = document.getElementById('serviceModal');
    const modalTitle = document.getElementById('serviceModalLabel');
    const modalContent = document.getElementById('serviceModalContent');

    // Định nghĩa cấu hình modal
    const modalConfig = {
        themMoi: {
            title: 'Thêm dịch vụ mới',
            url: '/admin/dichvu/view-them/'
        },
        chiSua: {
            title: 'Sửa dịch vụ',
            url: dichVuId ? `/admin/dichvu/view-sua/${dichVuId}/` : null
        }
    };

    // Kiểm tra loại modal hợp lệ
    const config = modalConfig[type];
    if (!config || (type === 'chiSua' && !dichVuId)) {
        modalTitle.textContent = 'Lỗi';
        modalContent.innerHTML = `
            <div class="p-4 bg-red-100 text-red-700 rounded text-center">
                Loại modal không hợp lệ hoặc thiếu ID dịch vụ.
            </div>
        `;
        modal.classList.remove('hidden');
        return;
    }

    // Hiển thị loading spinner
    modalTitle.textContent = config.title;
    modalContent.innerHTML = `
        <div class="text-center py-8">
            <div role="status" class="animate-spin rounded-full h-10 w-10 border-4 border-indigo-600 border-t-transparent mx-auto"></div>
            <span class="sr-only">Đang tải...</span>
        </div>
    `;
    modal.classList.remove('hidden');

    try {
        // Tải nội dung form
        const response = await fetch(config.url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest' // Đánh dấu là AJAX request
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
        }

        const html = await response.text();
        modalContent.innerHTML = html;

        // Khởi tạo sự kiện checkbox sau khi form được render
        if (typeof initCheckboxHandlers === 'function') {
            initCheckboxHandlers();
        }
    } catch (error) {
        console.error('Error loading modal content:', error);
        modalContent.innerHTML = `
            <div class="p-4 bg-red-100 text-red-700 rounded text-center">
                Không thể tải nội dung. Vui lòng thử lại sau (Lỗi: ${error.message}).
            </div>
        `;
    }
}
function XoaDichVu(dichVuId) {
    // Kiểm tra ID dịch vụ hợp lệ
    if (!dichVuId) {
        alert("ID dịch vụ không hợp lệ.");
        return;
    }
    // Xác nhận xóa
    if (confirm("Bạn có chắc chắn muốn xóa dịch vụ này?")) {
        // Gửi yêu cầu xóa dịch vụ
        fetch(`/dichvu/xoaDichVu/${dichVuId}`, {
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
function fetchThongKeDichVu() {
    let khuVuc = document.getElementById("khuVuc").value || "all"; // Nếu không chọn, mặc định là "all"
    const monthHidden = document.getElementById("month_hidden");
    const thang = monthHidden ? monthHidden.value : document.getElementById("month").value;
    const phongTro = document.getElementById('phongTro').value;
    
    const loaiDichVu = document.getElementById('loaiDichVu').value;
    if (!thang) {
        alert("Vui lòng chọn tháng!");
        return;
    }
    let url = `/admin/dichvu/thongke-dichvu?khuVuc=${khuVuc}&thang=${thang}&phongTro=${phongTro}&loaiDichVu=${loaiDichVu}`;
    fetch(url)
        .then((response) => {
            if (!response.ok) {
                throw new Error("HTTP error " + response.status);
            }
            return response.text();
        })
        .then((data) => {
            document.getElementById("table_thongke_dichvu").innerHTML = data;
        })
        .catch((error) => {
            console.error("Error loading thống kê dịch vụ:", error);
            document.getElementById("table_thongke_dichvu").innerHTML =
                '<div class="alert alert-danger">Không thể tải dữ liệu. Vui lòng thử lại sau.</div>';
        });
}
function exportExcel() {
    let khuVuc = document.getElementById("khuVuc").value || "all"; // Nếu không chọn, mặc định là "all"
    let thang = document.getElementById("month").value;

    if (!thang) {
        alert("Vui lòng chọn tháng!");
        return;
    }

    // Hiển thị hộp thoại nhập tên file
    let fileName = prompt("Nhập tên file (mặc định: ThongKeDichVu)", "ThongKeDichVu");
    if (fileName === null || fileName.trim() === "") {
        fileName = "ThongKeDichVu";
    }

    // Gửi yêu cầu tải file về
    fetch(`/admin/dichvu/xuat-thong-ke-dich-vu?khuVuc=${khuVuc}&thang=${thang}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Lỗi tải file");
            }
            return response.blob();  // Nhận dữ liệu dưới dạng blob
        })
        .then(blob => {
            // Tạo URL cho blob
            let url = window.URL.createObjectURL(blob);
            let a = document.createElement("a");
            a.href = url;
            a.download = `${fileName}.xlsx`; // Đặt tên file dựa vào input của người dùng
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);  // Xóa thẻ a sau khi tải
            window.URL.revokeObjectURL(url); // Giải phóng bộ nhớ
        })
        .catch(error => {
            console.error("Lỗi xuất file:", error);
            alert("Không thể tải file. Vui lòng thử lại.");
        });
}



