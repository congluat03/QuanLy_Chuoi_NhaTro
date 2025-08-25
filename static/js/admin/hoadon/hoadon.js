function toggleMenuHoaDon(khachThueId) {
    const menu = document.getElementById("menuHoaDon-" + khachThueId);

    // Ẩn tất cả các menu khác
    const allMenus = document.querySelectorAll("[id^='menuHoaDon-']");
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
