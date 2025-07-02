function toggleMenuQuanLy(khachThueId) {
    var menu = document.getElementById("menuQuanLy-" + khachThueId);

    // Lấy tất cả menu đang mở (không có class hidden)
    var allMenus = document.querySelectorAll("[id^='menuQuanLy-']");
    allMenus.forEach(function (m) {
        if (m !== menu) {
            m.classList.add("hidden");
            // Reset vị trí menu khi ẩn
            m.style.top = '';
            m.style.bottom = '';
        }
    });

    // Kiểm tra trạng thái hiện tại của menu
    var isHidden = menu.classList.contains("hidden");

    if (isHidden) {
        // Menu đang ẩn, mở menu

        // Reset vị trí menu ban đầu
        menu.style.top = '';
        menu.style.bottom = '';

        // Tính vị trí menu có bị che khuất dưới cùng không
        var rect = menu.getBoundingClientRect();
        var windowHeight = window.innerHeight;

        if (rect.bottom > windowHeight) {
            // Nếu bị che, đổi vị trí lên trên
            menu.style.top = 'auto';
            menu.style.bottom = '35px';
        } else {
            // Vị trí mặc định dưới icon
            menu.style.top = '35px';
            menu.style.bottom = 'auto';
        }

        // Hiển thị menu
        menu.classList.remove("hidden");

        // Thêm sự kiện mouseleave để tự động ẩn menu khi chuột rời menu
        menu.onmouseleave = function() {
            menu.classList.add("hidden");
            // Reset vị trí menu khi ẩn
            menu.style.top = '';
            menu.style.bottom = '';
            // Hủy sự kiện sau khi ẩn menu để tránh bị gọi lại nhiều lần
            menu.onmouseleave = null;
        };
    } else {
        // Menu đang hiện, ẩn menu
        menu.classList.add("hidden");
        menu.style.top = '';
        menu.style.bottom = '';
        menu.onmouseleave = null;
    }
}


// Hàm ẩn menu khi chuột rời menu dropdown
function hideMenuQuanLy(khachThueId) {
    var menu = document.getElementById("menuQuanLy-" + khachThueId);
    if (menu) {
        menu.style.display = "none";
        // Reset vị trí menu
        menu.style.top = '35px';
        menu.style.bottom = 'auto';
    }
}

document.addEventListener("click", function (event) {
    var isClickInsideMenu = event.target.closest(".tooltipQuanLy"); // Biểu tượng 3 chấm
    var isClickInsideBox = event.target.closest(".khuvuc-card");

    // Nếu click không phải vào .khuvuc-card hoặc .menu-icon thì ẩn tất cả các menu
    if (!isClickInsideMenu && !isClickInsideBox) {
        var menus = document.querySelectorAll(".menu-items");
        menus.forEach(function (menu) {
            menu.style.display = "none";
        });
    }
});

function showChucNangQuanLy(type, khachThueId) {
    let url = "";
    let initFunction = null;

    switch (type) {
        case "chitiet":
            url = "/nhanvien/viewThietLapTaiKhoan/" + khachThueId;
            break;
        case "chinhsua":
            url = "/nhanvien/viewSuaNhanVien/" + khachThueId;
            break;
        case "thietlaptaikhoan":
            url = "/nhanvien/viewThietLapTaiKhoan/" + khachThueId;
            break;
        default:
            console.log("Invalid type");
            return;
    }

    // Giao diện chờ theo Tailwind
    document.getElementById("modalContentQuanLy").innerHTML = `
        <div class="text-center py-6">
            <div class="inline-block animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full"></div>
            <p class="mt-3 text-sm text-gray-500">Đang tải...</p>
        </div>
    `;

    // Hiển thị modal Tailwind
    document.getElementById("quanlyModal").classList.remove("hidden");

    // Tải nội dung động từ server
    fetch(url)
        .then((response) => {
            if (!response.ok) {
                throw new Error("HTTP error " + response.status);
            }
            return response.text();
        })
        .then((data) => {
            document.getElementById("modalContentQuanLy").innerHTML = data;
            if (initFunction) initFunction();
        })
        .catch((error) => {
            console.error("Error loading modal content:", error);
            document.getElementById("modalContentQuanLy").innerHTML = `
                <div class="p-4 bg-red-100 text-red-700 rounded-lg text-sm text-center">
                    Không thể tải nội dung. Vui lòng thử lại sau.
                </div>
            `;
        });
}
function toggleQuanlyModal(show) {
    const modal = document.getElementById("quanlyModal");
    if (show) {
        modal.classList.remove("hidden");
    } else {
        modal.classList.add("hidden");
    }
}

function XoaQuanLy(quanLyId) {
    // Kiểm tra ID Quản lý hợp lệ
    if (!quanLyId) {
        alert("ID Quản lý không hợp lệ.");
        return;
    }
    // Xác nhận xóa
    if (confirm("Bạn có chắc chắn muốn xóa Quản lý này?")) {
        // Gửi yêu cầu xóa Quản lý
        fetch(`/nhanvien/xoaNhanvien/${quanLyId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Nếu xóa thành công, thông báo và tải lại trang
                    alert(data.message);
                    location.reload();
                } else {
                    // Nếu có lỗi khi xóa, thông báo lỗi
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Có lỗi xảy ra, vui lòng thử lại!');
            });
    }
}
