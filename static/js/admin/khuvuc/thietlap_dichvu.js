function intThietLapDichVu() {
    const forms = document.querySelectorAll('form[method="POST"]');
    forms.forEach((form) => {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.dataset.originalText = submitButton.innerHTML; // Lưu văn bản gốc
            submitButton.innerHTML =
                '<i class="fas fa-spinner fa-spin mr-1 text-sm"></i> Đang xử lý...';
            fetch(form.action, {
                method: "POST",
                body: new FormData(form),
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            }).then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
            })
                .then((data) => {
                    if (data.status === "success") {
                        
                        // Tải lại nội dung modal
                        showModalKhuvuc(
                            "thietLapDichVu",
                            form.querySelector('input[name="khuvuc_id"]').value
                        );
                        showSuccessMessage(data.message);
                    } else {
                        showErrorMessage(
                            data.message || "Có lỗi xảy ra. Vui lòng thử lại."
                        );
                        submitButton.disabled = false;
                        submitButton.innerHTML = submitButton.dataset.originalText;
                    }
                })
                .catch((error) => {
                    console.error("Error:", error);
                    showErrorMessage("Lỗi kết nối hoặc xử lý. Vui lòng thử lại.");
                    submitButton.disabled = false;
                    submitButton.innerHTML = submitButton.dataset.originalText;
                });
        });
    });
}
function showSuccessMessage(message) {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'flex items-center gap-2 p-3 rounded-lg shadow-sm border-l-4 bg-green-50 border-green-600 text-green-800';
    messageContainer.innerHTML = `
        <i class="fas fa-check-circle text-base"></i>
        <span class="flex-1 text-sm">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-gray-500 hover:text-gray-700">
            <i class="fas fa-times text-sm"></i>
        </button>
    `;
    document.querySelector('.mb-4').prepend(messageContainer);
    setTimeout(() => messageContainer.remove(), 5000);
}

function showErrorMessage(message) {
    const messageContainer = document.createElement("div");
    messageContainer.className =
        "flex items-center gap-2 p-3 rounded-lg shadow-sm border-l-4 bg-red-50 border-red-600 text-red-800";
    messageContainer.innerHTML = `
        <i class="fas fa-times-circle text-base"></i>
        <span class="flex-1 text-sm">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-gray-500 hover:text-gray-700">
            <i class="fas fa-times text-sm"></i>
        </button>
    `;
    document.querySelector(".mb-4").prepend(messageContainer);
    setTimeout(() => messageContainer.remove(), 5000);
}


function showConfirmModal(dichVuId, lichSuId, khuvucID, action, url) {
    // Gán dữ liệu vào các input hidden
    document.getElementById("inputDichVuId").value = dichVuId;
    document.getElementById("inputLichSuId").value = lichSuId;
    document.getElementById("inputAction").value = action;
       document.getElementById("inputKhuVucid").value = khuvucID;

    // Gán URL vào form
    document.getElementById("confirmForm").action = url;

    // Hiển thị modal
    document.getElementById("confirmModal").classList.remove("hidden");
}

function closeConfirmModal() {
    document.getElementById("confirmModal").classList.add("hidden");
}

function disableConfirmButton() {
    const btn = document.getElementById("confirmButton");
    btn.disabled = true;
    btn.innerHTML =
        '<i class="fas fa-spinner fa-spin mr-1 text-sm"></i> Đang xử lý...';
}

function filterDichVu(searchTerm, statusFilter = "") {
    const dichVus = document.querySelectorAll("[data-dich-vu]");
    dichVus.forEach((dichVu) => {
        const name = dichVu.dataset.name.toLowerCase();
        const status = dichVu.dataset.status;
        const matchesSearch = searchTerm
            ? name.includes(searchTerm.toLowerCase())
            : true;
        const matchesStatus = statusFilter === "" || status === statusFilter;
        dichVu.style.display = matchesSearch && matchesStatus ? "" : "none";
    });
}
