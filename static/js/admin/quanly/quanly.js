function toggleMenuQuanLy(managerId) {
    const menu = document.getElementById("menuQuanLy-" + managerId);

    // Ẩn tất cả các menu khác
    const allMenus = document.querySelectorAll("[id^='menuQuanLy-']");
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

// Hàm ẩn menu khi chuột rời menu dropdown
function hideMenuQuanLy(managerId) {
    const menu = document.getElementById("menuQuanLy-" + managerId);
    if (menu) {
        menu.classList.add("hidden");
        menu.onmouseleave = null;
    }
}

document.addEventListener("click", function (event) {
    var isClickInsideMenu = event.target.closest(".tooltipQuanLy"); // Biểu tượng 3 chấm
    var isClickInsideDropdown = event.target.closest("[id^='menuQuanLy-']"); // Menu dropdown

    // Nếu click không phải vào button hoặc menu thì ẩn tất cả các menu
    if (!isClickInsideMenu && !isClickInsideDropdown) {
        const allMenus = document.querySelectorAll("[id^='menuQuanLy-']");
        allMenus.forEach((menu) => {
            menu.classList.add("hidden");
            menu.onmouseleave = null;
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
