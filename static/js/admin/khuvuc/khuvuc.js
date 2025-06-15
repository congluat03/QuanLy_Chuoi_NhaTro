function toggleMenuKhuVuc(khuVucId) {
    const menu = document.getElementById(`menuKhuVuc-${khuVucId}`);
    const allMenus = document.querySelectorAll("[id^='menuKhuVuc-']");

    // Tìm đúng button theo onclick
    const button = document.querySelector(`button[onclick="toggleMenuKhuVuc('${khuVucId}')"]`);
    const card = button.closest("div.relative") || button.parentElement;

    if (menu.classList.contains("hidden")) {
        // Ẩn tất cả các menu khác
        allMenus.forEach(m => {
            m.classList.add("hidden");
            m.classList.remove("animate-fadeIn");
        });

        // Hiện menu hiện tại
        menu.classList.remove("hidden");
        menu.classList.add("animate-fadeIn");

        // Điều chỉnh vị trí tránh tràn màn hình
        const menuRect = menu.getBoundingClientRect();
        const viewportWidth = window.innerWidth;

        if (menuRect.right > viewportWidth - 10) {
            menu.classList.remove("right-0");
            menu.classList.add("left-0");
            menu.style.transform = `translateX(-${menuRect.width - button.offsetWidth}px)`;
        } else {
            menu.classList.add("right-0");
            menu.classList.remove("left-0");
            menu.style.transform = "";
        }

        if (menuRect.bottom > window.innerHeight - 10) {
            menu.classList.remove("top-12");
            menu.classList.add("bottom-12");
        } else {
            menu.classList.add("top-12");
            menu.classList.remove("bottom-12");
        }

        // Tự động ẩn menu khi chuột rời khỏi
        menu.onmouseleave = function () {
            menu.classList.add("hidden");
            menu.classList.remove("animate-fadeIn");
        };
    } else {
        // Đóng menu hiện tại
        menu.classList.add("hidden");
        menu.classList.remove("animate-fadeIn");
    }
}

// Thêm sự kiện click để ẩn menu nếu click ra ngoài
document.addEventListener("click", function (event) {
    const isClickInsideMenu = event.target.closest("button[aria-label='Mở menu thao tác khu vực']");
    const isClickInsideBox = event.target.closest(".khuvuc-content");

    // Nếu click không phải vào button hoặc khu vực card thì ẩn tất cả các menu
    if (!isClickInsideMenu && !isClickInsideBox) {
        const menus = document.querySelectorAll("[id^='menuKhuVuc-']");
        menus.forEach(function (menu) {
            menu.classList.add("hidden");
            menu.classList.remove("animate-fadeIn");
        });
    }
});

function showModalKhuvuc(type, khuVucId = null) {
    let url = "";
    let initFunction = null;

    switch (type) {
        case "thongTin":
            url = `/admin/khuvuc/thong-tin/${khuVucId}/`;
            initFunction = initThongTin;
            break;
        case "chiSua":
            url = `/admin/khuvuc/sua/${khuVucId}/`;
            break;
        case "thietLapDichVu":
            url = `/admin/khuvuc/thiet-lap-dich-vu/${khuVucId}/`;
            initFunction = initThietLapDichVu;
            break;
        case "thietLapNguoiQuanLy":
            url = `/admin/khuvuc/thiet-lap-nguoi-quan-ly/${khuVucId}/`;
            break;
        case "themKhuVuc":
            url = "/admin/khuvuc/them/";
            break;
    }

    // Ẩn menu nếu đang mở
    const menu = document.getElementById(`menuKhuVuc-${khuVucId}`);
    if (menu) {
        menu.classList.add("hidden");
        menu.classList.remove("animate-fadeIn");
    }

    // Loading spinner giao diện Tailwind
    document.getElementById("modalContentKhuVuc").innerHTML = `
        <div class="text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p class="text-indigo-700">Đang tải thông tin khu vực...</p>
        </div>
    `;

    const modal = document.getElementById("khuVucModal");
    if (modal) {
        modal.classList.remove("hidden");
    }

    fetch(url)
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.text();
        })
        .then((data) => {
            document.getElementById("modalContentKhuVuc").innerHTML = data;
            if (typeof initFunction === "function") {
                initFunction();
            }
        })
        .catch((error) => {
            console.error("Error loading modal content:", error);
            document.getElementById("modalContentKhuVuc").innerHTML = `
                <div class="text-red-600 text-center p-4 bg-red-100 rounded">
                    Không thể tải nội dung. Vui lòng thử lại sau.
                </div>
            `;
        });
}
function toggleKhuVucModal(show) {
    const modal = document.getElementById("khuVucModal");
    if (modal) {
        modal.classList.toggle("hidden", !show);
    }
}
