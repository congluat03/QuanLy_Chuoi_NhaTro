const monthButtons = document.querySelectorAll(".month-btn");
const prevYearButton = document.getElementById("prev-year");
const nextYearButton = document.getElementById("next-year");
const activeMonthButton = document.querySelector(".month-btn.active");

monthButtons.forEach((button) => {
    button.addEventListener("click", function () {
        const month = this.dataset.month;
        const year = this.dataset.year;
        window.location.href =
            "/hoadon/allHoaDon?month=" + month + "&year=" + year;
    });
});

prevYearButton.addEventListener("click", function () {
    const currentYear = parseInt(activeMonthButton.dataset.year);
    window.location.href = "/hoadon/allHoaDon?month=12&year=" + (currentYear - 1);
});

nextYearButton.addEventListener("click", function () {
    const currentYear = parseInt(activeMonthButton.dataset.year);
    window.location.href = "/hoadon/allHoaDon?month=1&year=" + (currentYear + 1);
});
document.addEventListener('click', function (e) {
    if (!e.target.closest('.tooltipHoaDon') && !e.target.closest('.menu-items')) {
        document.querySelectorAll('.menu-items').forEach(menu => {
            menu.classList.add('hidden');
        });
    }
});
function toggleMenuHoaDon(maHoaDon) {
    const menu = document.getElementById(`menuHoaDon-${maHoaDon}`);
    const isVisible = !menu.classList.contains('hidden');

    // Đóng tất cả các menu khác
    document.querySelectorAll('.menu-items').forEach(m => {
        m.classList.add('hidden');
        m.classList.remove('show');
    });

    if (!isVisible) {
        // Tính toán vị trí menu
        const rect = menu.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        const isOverflowing = rect.bottom > windowHeight - 20; // 20px khoảng đệm

        // Điều chỉnh vị trí hiển thị
        if (isOverflowing) {
            menu.style.top = 'auto';
            menu.style.bottom = '100%';
            menu.style.marginTop = '0';
            menu.style.marginBottom = '8px'; // Tương đương với mb-2
        } else {
            menu.style.top = '100%';
            menu.style.bottom = 'auto';
            menu.style.marginTop = '8px'; // mt-2
            menu.style.marginBottom = '0';
        }

        // Hiển thị menu
        menu.classList.remove('hidden');
        setTimeout(() => menu.classList.add('show'), 10); // Hiệu ứng chuyển mượt
    }
}


document.addEventListener("click", function (event) {
    var isClickInsideMenu = event.target.closest(".tooltipHoaDon"); // Biểu tượng 3 chấm
    var isClickInsideBox = event.target.closest(".khuvuc-card");

    // Nếu click không phải vào .khuvuc-card hoặc .menu-icon thì ẩn tất cả các menu
    if (!isClickInsideMenu && !isClickInsideBox) {
        var menus = document.querySelectorAll(".menu-items");
        menus.forEach(function (menu) {
            menu.style.display = "none";
        });
    }
});

function getUrlForType(type, khachThueId) {
    switch (type) {
        case "chitiet":
            return "/hoadon/viewChiTietHoaDon/" + khachThueId;
        case "chinhsua":
            return "/hoadon/viewSuaHoaDon/" + khachThueId;
        default:
            console.log("Invalid type");
            return null;
    }
}

function toggleHoaDonModal(show) {
    const modal = document.getElementById("hoaDonModal");
    if (show) {
        modal.classList.remove("hidden");
    } else {
        modal.classList.add("hidden");
    }
}

function showModal() {
    // Hiển thị giao diện loading Tailwind
    document.getElementById("modalContentHoaDon").innerHTML = `
        <div class="text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-700 mx-auto mb-4"></div>
            <p class="text-blue-700">Đang tải thông tin hóa đơn...</p>
        </div>
    `;

    // Mở modal
    toggleHoaDonModal(true);
}

function loadAndDisplayData(url, initFunction) {
    fetch(url)
        .then((response) => {
            if (!response.ok) {
                throw new Error("HTTP error " + response.status);
            }
            return response.text();
        })
        .then((data) => {
            document.getElementById("modalContentHoaDon").innerHTML = data;
            if (initFunction) initFunction();
        })
        .catch((error) => {
            console.error("Error loading modal content:", error);
            document.getElementById("modalContentHoaDon").innerHTML = `
                <div class="bg-red-100 text-red-700 px-4 py-3 rounded text-center">
                    Không thể tải nội dung. Vui lòng thử lại sau.
                </div>
            `;
        });
}

function showChucNangHoaDon(type, khachThueId) {
    const url = getUrlForType(type, khachThueId);
    alert(url);
    if (!url) return;

    showModal();
    loadAndDisplayData(url, null);
}


// Tính số dịch vụ tổng (chênh lệch giữa CHISOMOI và CHISOCU)
function tinhSodichvuTong(chisocu, chisomoi) {
    return Math.max(chisomoi - chisocu, 0); // Số dịch vụ không thể nhỏ hơn 0
}

// Tính thành tiền dịch vụ (SODICHVUTONG * GIADICHVU)
function tinhTienDichVu(sodichvuTong, giaDichVu) {
    return sodichvuTong * giaDichVu;
}
// Cập nhật UI cho các trường số dịch vụ tổng và thành tiền khi CHISOMOI thay đổi
function capNhatUI(madichvukhucvuc, giaDichVu) {
    const chisocuInput = document.getElementById(`CHISOCU-${madichvukhucvuc}`);
    const chisomoiInput = document.getElementById(
        `CHISOMOI-${madichvukhucvuc}`
    );
    const sodichvuTongInput = document.getElementById(
        `SODICHVUTONG-${madichvukhucvuc}`
    );
    const tiendichvuGhiDuocInput = document.getElementById(
        `TIENDICHVUGHIDUOC-${madichvukhucvuc}`
    );

    chisomoiInput.addEventListener("input", function () {
        const chisocu = parseFloat(chisocuInput.value) || 0; // Nếu không phải số thì mặc định là 0
        const chisomoi = parseFloat(chisomoiInput.value) || 0;

        // Tính số dịch vụ tổng và thành tiền dịch vụ
        const sodichvuTong = tinhSodichvuTong(chisocu, chisomoi);
        sodichvuTongInput.value = sodichvuTong.toFixed(2); // Hiển thị 2 chữ số thập phân

        const tiendichvu = tinhTienDichVu(sodichvuTong, giaDichVu);
        tiendichvuGhiDuocInput.value = tiendichvu.toFixed(2);
    });
}
// Hàm gửi yêu cầu cập nhật cơ sở dữ liệu
function capNhatCoSoDuLieu(
    madichvukhucvuc,
    chisomoi,
    sodichvuTong,
    tiendichvuGhiDuoc
) {
    return fetch(`/hoadon/chisodichvu/capNhatChiSo/${madichvukhucvuc}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": document
                .querySelector('meta[name="csrf-token"]')
                .getAttribute("content"),
        },
        body: JSON.stringify({
            CHISOMOI: chisomoi,
            SODICHVUTONG: sodichvuTong,
            TIENDICHVUGHIDUOC: tiendichvuGhiDuoc,
        }),
    })
        .then((response) => response.json())
        .then((data) => {
            return data;
        })
        .catch((error) => {
            console.error("Lỗi khi gửi yêu cầu cập nhật:", error);
            throw error;
        });
}
