document.addEventListener("DOMContentLoaded", function () {
    // Thêm sự kiện click vào các liên kết phân trang
    const paginationLinks = document.querySelectorAll(".pagination a");
    paginationLinks.forEach((link) => {
        link.addEventListener("click", function (e) {
            e.preventDefault(); // Ngăn hành vi mặc định của link

            // Lấy mã khu vực từ tab đang active
            const activeTab = document.querySelector(".khuvuc-tab.bg-blue-600");
            const maKhuVuc = activeTab ? activeTab.getAttribute("data-makhuvuc") : null;

            // Lấy số trang từ URL của liên kết phân trang
            const page = new URL(link.href).searchParams.get("page");

            // Gọi hàm AJAX để tải dữ liệu phòng trọ
            if (maKhuVuc) {
                loadPhongTro(maKhuVuc, page);
            }
        });
    });
});


function loadPhongTro(maKhuVuc, page = 1) {
    const url = `/admin/phongtro/?${maKhuVuc}&${page}`;
    fetch(url)
        .then((response) => response.text())
        .then((html) => {
            document.getElementById("phong-tro-content").innerHTML = html;
        })
        .catch((error) => console.error("Error:", error));
}

function toggleMenuPhongTro(phongTroId) {
    const menu = document.getElementById(`menuPhongTro-${phongTroId}`);
    const allMenus = document.querySelectorAll("[id^='menuPhongTro-']");
    const button = document.querySelector(`button[onclick='toggleMenuPhongTro(${phongTroId})']`);
    const card = button.closest("div.relative");

    // Toggle menu visibility
    if (menu.classList.contains("hidden")) {
        // Hide all other menus
        allMenus.forEach((m) => {
            m.classList.add("hidden");
            m.classList.remove("animate-fadeIn");
        });

        // Show current menu
        menu.classList.remove("hidden");
        menu.classList.add("animate-fadeIn");

        // Prevent overflow by adjusting menu position
        const menuRect = menu.getBoundingClientRect();
        const cardRect = card.getBoundingClientRect();
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

        // 👇 Add event to auto close when mouse leaves the menu
        menu.onmouseleave = function () {
            menu.classList.add("hidden");
            menu.classList.remove("animate-fadeIn");
        };
    } else {
        // Hide current menu
        menu.classList.add("hidden");
        menu.classList.remove("animate-fadeIn");
    }
}
function togglePhongTroModal(show) {
    const modal = document.getElementById("phongTroModal");
    if (show) {
        modal.classList.remove("hidden");
    } else {
        modal.classList.add("hidden");
    }
}


// 👉 Hàm chính: gọi các hàm nhỏ để hiển thị modal phòng trọ
function showModalPhongTro(type, maPhongTro = null, khuVucId = null, tenPhong = null) {
    const modalLabel = document.getElementById("phongTroModalLabel");
    const modalContentId = "modalContentPhongTro";

    const url = getModalUrl(type, khuVucId, maPhongTro);
    if (!url) {
        console.error("Invalid modal type:", type);
        return;
    }
    // alert(url);
    modalLabel.innerText = getModalTitle(type, maPhongTro, tenPhong);
    hidePhongTroMenu(khuVucId, maPhongTro);
    
    showLoadingSpinner(modalContentId);
   
    openModal("phongTroModal", type);
    
    loadModalContent(url, modalContentId, type);
}
// Hàm lấy URL tương ứng theo loại modal
function getModalUrl(type, khuVucId, maPhongTro) {
    return {
        HopDong: `/admin/phongtro/lap-hop-dong/${maPhongTro}`,
        ChonHoaDon: `/admin/hoadon/them/${maPhongTro}/`,
        CoPhong: `/admin/phongtro/coc-giu-cho/${maPhongTro}/`,
        info: `/admin/phongtro/viewInfo/${maPhongTro}`,
        chinhsua: `/admin/phongtro/view-themsua-phongtro/${khuVucId}/edit/${maPhongTro}`,
        them: `/admin/phongtro/view-themsua-phongtro/${khuVucId}/single`,
        themnhieu: `/admin/phongtro/view-themsua-phongtro/${khuVucId}/multiple`,
        ghi_so_dich_vu: `/admin/phongtro/ghi-so-dich-vu/${maPhongTro}`,
    }[type] || null;
}
// Hàm tải và hiển thị nội dung modal
function loadModalContent(url, containerId, type) {
    fetch(url)
        .then(response => response.ok ? response.text() : Promise.reject(new Error(`HTTP error! Status: ${response.status}`)))
        .then(data => {
            const container = document.getElementById(containerId);
            container.innerHTML = data;
            // Tìm tất cả thẻ <script> trong HTML mới
            const scripts = container.querySelectorAll("script");

            scripts.forEach((script) => {
                const newScript = document.createElement("script");

                // Nếu là script có src (file js)
                if (script.src) {
                    newScript.src = script.src;
                } else {
                    newScript.textContent = script.textContent;
                }

                // Sao chép các thuộc tính khác (nếu cần)
                if (script.type) newScript.type = script.type;

                // Gắn vào DOM để thực thi
                document.head.appendChild(newScript);
            });
            // const initFn = initFunctions[type];
            // if (typeof initFn === "function") {
            //     initFn(); // gọi hàm khởi tạo nếu có
            // }
        })
        .catch(error => {
            console.error("Error loading modal content:", error);
            showErrorMessage(containerId, error);
        });
}
// Hàm tiện ích mở modal
function openModal(modalId, type) {  
    const modal = document.getElementById(modalId);
    const modalContainer = document.getElementById("modalContainerPT");
    if (modalContainer) {
        // Mặc định là max-w-2xl (khoảng 672px)
        modalContainer.classList.remove("max-w-3xl", "max-w-6xl");
        if (type === "HopDong" || type === "ChonHoaDon") {
            modalContainer.classList.add("max-w-6xl");
        } else {
            modalContainer.classList.add("max-w-3xl");
        }
    }


    modal.classList.remove("hidden");
    // modal.classList.add("flex");
}

// Hàm hiển thị spinner loading
function showLoadingSpinner(containerId) {
    document.getElementById(containerId).innerHTML = `
        <div class="flex justify-center items-center py-10">
            <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900"></div>
        </div>`;
}


// Hàm lấy tiêu đề modal
function getModalTitle(type, maPhongTro, tenPhong) {
    if (["edit", "single", "multiple"].includes(type)) {
        return maPhongTro ? `Chỉnh sửa phòng: ${tenPhong}` : `Thêm ${type === "single" ? "mới" : "nhiều"} phòng trọ`;
    }
    return {
        HopDong: "Lập hợp đồng",
        ChonHoaDon: "Lập hóa đơn",
        CoPhong: "Thêm Cọc Giữ Chỗ - Phòng "+ tenPhong,
        info: "Thông tin phòng trọ"
    }[type] || "Thông tin";
}

// Hàm ẩn menu popup nếu có
function hidePhongTroMenu(khuVucId, maPhongTro) {
    const menuId = `menuPhongTro-${maPhongTro || khuVucId}`;
    const menu = document.getElementById(menuId);
    if (menu) menu.classList.add("hidden");
}




function XoaPhongTro(maPhongTro) {
    // Kiểm tra ID phòng trọ hợp lệ
    if (!maPhongTro) {
        alert("ID phòng trọ không hợp lệ.");
        return;
    }

    // Xác nhận xóa
    if (confirm("Bạn có chắc chắn muốn xóa phòng trọ này?")) {
        // Gửi yêu cầu xóa phòng trọ
        fetch(`/phongtro/xoaPhongTro/${maPhongTro}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-TOKEN": document
                    .querySelector('meta[name="csrf-token"]')
                    .getAttribute("content"),
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    // Nếu xóa thành công, thông báo và làm mới danh sách
                    alert(data.message);
                    location.reload(); // Tải lại trang
                } else {
                    // Thông báo lỗi nếu không xóa được
                    alert(data.message || "Không thể xóa phòng trọ.");
                }
            })
            .catch((error) => {
                console.error("Error:", error);
                alert("Có lỗi xảy ra, vui lòng thử lại!", error);
            });
    } else {
        return;
    }
}
