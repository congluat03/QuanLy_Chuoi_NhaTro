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
    // Đặt kích thước modal
    const modalContainer = document.getElementById("modalContainer");
    if (modalContainer) {
        // Mặc định là max-w-2xl (khoảng 672px)
        modalContainer.classList.remove("max-w-2xl", "max-w-4xl", "max-w-6xl");
        if (type === "thietLapDichVu") {
            // Tăng kích thước cho thiết lập dịch vụ (max-w-4xl ≈ 896px)
            modalContainer.classList.add("max-w-4xl");
        } else if (type === "themKhuVuc" || type === "chiSua") {
            // Tăng kích thước cho form thêm/sửa khu vực (max-w-6xl ≈ 1152px)
            modalContainer.classList.add("max-w-6xl");
        } else {
            modalContainer.classList.add("max-w-2xl");
        }
    }
    switch (type) {
        case "thongTin":
            url = `/admin/khuvuc/thong-tin/${khuVucId}/`;
            initFunction = initThongTin;
            break;
        case "suaKhuVuc":
            url = `/admin/khuvuc/sua/${khuVucId}/`;
            initFunction = initModalMap;
            break;

        case "thietLapDichVu":
            url = `/admin/khuvuc/thiet-lap-dich-vu/${khuVucId}/`;
            initFunction = intThietLapDichVu;
            break;
        case "dungQuanLy":
            url = `/admin/khuvuc/dung_quanly/${khuVucId}/`;
            break;
        case "thietLapNguoiQuanLy":
            url = `/admin/khuvuc/thiet-lap-nguoi-quan-ly/${khuVucId}/`;
            break;
        case "themKhuVuc":
            url = "/admin/khuvuc/them/";
            initFunction = initModalMap;
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

    fetch(url, {
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            if (data.error) {
                throw new Error(data.error);
            }
            document.getElementById("modalContentKhuVuc").innerHTML = data.html;
            
            // Khởi tạo OpenStreetMap modal nếu có
            if (typeof initFunction === "function") {
                // Đợi một chút để DOM được render
                setTimeout(() => {
                    initFunction();
                }, 100);
            }
            
            // Thiết lập xử lý form submission qua AJAX
            setupModalFormSubmission();
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
        
        // Cleanup map khi đóng modal
        if (!show && typeof cleanupModalMap === "function") {
            cleanupModalMap();
        }
    }
}

function setupModalFormSubmission() {
    const form = document.getElementById('khuVucForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const action = form.action || (form.querySelector('input[name="MA_KHU_VUC"]') ? 
            `/admin/khuvuc/sua/${form.querySelector('input[name="MA_KHU_VUC"]').value}/` : 
            '/admin/khuvuc/them/');
        
        fetch(action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Hiển thị thông báo thành công
                showSuccessMessage(data.message);
                
                // Đóng modal
                toggleKhuVucModal(false);
                
                // Reload trang để cập nhật danh sách
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error(data.message || 'Có lỗi xảy ra');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorMessage(error.message || 'Có lỗi xảy ra khi lưu khu vực');
        });
    });
}

function showSuccessMessage(message) {
    const alert = document.createElement('div');
    alert.className = 'fixed top-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10001] flex items-center';
    alert.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (document.body.contains(alert)) {
            document.body.removeChild(alert);
        }
    }, 3000);
}

function showErrorMessage(message) {
    const alert = document.createElement('div');
    alert.className = 'fixed top-4 right-4 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg z-[10001] flex items-center';
    alert.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        if (document.body.contains(alert)) {
            document.body.removeChild(alert);
        }
    }, 5000);
}

