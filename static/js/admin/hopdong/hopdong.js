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

