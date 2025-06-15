function toggleMenuKhachThue(khachThueId) {
    const menu = document.getElementById(`menuKhachThue-${khachThueId}`);
    const isVisible = !menu.classList.contains('hidden');

    // Close all other menus
    document.querySelectorAll('.menu-items').forEach(m => {
        m.classList.add('hidden');
        m.classList.remove('show');
    });

    if (!isVisible) {
        // Check if menu would be cut off at the bottom
        const rect = menu.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        const isOverflowing = rect.bottom > windowHeight - 20;

        // Adjust positioning with Tailwind-compatible classes
        menu.classList.remove('top-full', 'bottom-full', 'mt-2', 'mb-2');
        if (isOverflowing) {
            menu.classList.add('bottom-full', 'mb-2');
        } else {
            menu.classList.add('top-full', 'mt-2');
        }

        // Show the menu
        menu.classList.remove('hidden');
        setTimeout(() => menu.classList.add('show'), 10);
    }
}

function showChucNangKhachThue(type, khachThueId = null) {
    
    let url = "";
    let initFunction = null;

    switch (type) {
        case "chitiet":
            url = `/khach-thue/chi-tiet/${khachThueId}/`;
            initFunction = initThongTin;
            break;
        case "chinhsua":
            url = `/admin/khachthue/viewsua/${khachThueId}/`;
            initFunction = initChiSua;
            break;
        case "them":
            url = `/admin/khachthue/viewthem/`;
            initFunction = initThongTin;
            break;
        default:
            console.log("Invalid type");
            return;
    }
    // Show loading in modal
    const modalContent = document.getElementById("modalContentKhachThue");
    modalContent.innerHTML = `
        <div class="text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-700 mx-auto mb-4"></div>
            <p class="text-blue-700">Đang tải thông tin khách thuê...</p>
        </div>
    `;

    // Open modal
    toggleKhachThueModal(true);

    // Fetch content
    fetch(url, {
        headers: {
            'X-CSRFToken': getCsrfToken()
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.text();
        })
        .then(data => {
            modalContent.innerHTML = data;
            if (initFunction) initFunction();
        })
        .catch(error => {
            console.error("Error loading modal content:", error);
            modalContent.innerHTML = `
                <div class="text-red-600 text-center bg-red-100 border border-red-300 rounded-lg p-4">
                    Không thể tải nội dung. Vui lòng thử lại sau.
                </div>
            `;
        });
}

function toggleKhachThueModal(show) {
    const modal = document.getElementById("khachThueModal");
    modal.classList.toggle('hidden', !show);
}

function XoaKhachThue(khachThueId) {
    if (!khachThueId) {
        alert("ID khách thuê không hợp lệ.");
        return;
    }
    if (confirm("Bạn có chắc chắn muốn xóa khách thuê này?")) {
        fetch(`/khach-thue/xoa/${khachThueId}/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    location.reload();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Có lỗi xảy ra, vui lòng thử lại!');
            });
    }
}

function getCsrfToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function initChiSua() {
    // Placeholder for edit form initialization (e.g., bind form submission)
    console.log("Initializing edit form");
}

function initThongTin() {
    // Placeholder for detail view initialization
    console.log("Initializing detail view");
}

function toggleRoomList() {
    const roomHeaders = document.querySelectorAll(".room-header");

    roomHeaders.forEach(header => {
        let nextRow = header.nextElementSibling;

        // Default: show all tenant rows
        while (nextRow && !nextRow.classList.contains("room-header")) {
            nextRow.style.display = "table-row";
            nextRow = nextRow.nextElementSibling;
        }

        // Toggle on click
        header.addEventListener("click", () => {
            const isOpen = !header.classList.contains("closed");
            let nextRow = header.nextElementSibling;

            while (nextRow && !nextRow.classList.contains("room-header")) {
                nextRow.style.display = isOpen ? "none" : "table-row";
                nextRow = nextRow.nextElementSibling;
            }

            header.classList.toggle("closed", isOpen);
        });
    });
}

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    toggleRoomList();

    // Close menus when clicking outside
    document.addEventListener('click', event => {
        const isClickInside = event.target.closest('.menu-items') || event.target.closest('.cursor-pointer');
        if (!isClickInside) {
            document.querySelectorAll('.menu-items').forEach(menu => {
                menu.classList.add('hidden');
                menu.classList.remove('show');
            });
        }
    });
});