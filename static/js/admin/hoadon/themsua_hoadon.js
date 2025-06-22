// Hàm quản lý quá trình chỉnh sửa và lưu chỉ số dịch vụ
function ChinhSuaChiSoDichVU(madichvukhucvuc, giaDichVu) {
    const button = document.getElementById(`button-${madichvukhucvuc}`);
    const inputChiSoMoi = document.getElementById(
        `CHISOMOI-${madichvukhucvuc}`
    );
    const inputChiSoCu = document.getElementById(`CHISOCU-${madichvukhucvuc}`);
    const inputSoDichVuTong = document.getElementById(
        `SODICHVUTONG-${madichvukhucvuc}`
    );
    const inputTienDichVuGhiDuoc = document.getElementById(
        `TIENDICHVUGHIDUOC-${madichvukhucvuc}`
    );

    // Kiểm tra trạng thái nút
    if (button.dataset.status === "1") {
        // Trạng thái chỉnh sửa
        inputChiSoMoi.disabled = false;
        button.textContent = "Lưu";
        button.classList.remove("btn-danger");
        button.classList.add("btn-success");
        button.dataset.status = "2"; // Đặt trạng thái là lưu

        // Lắng nghe sự kiện khi thay đổi giá trị CHISOMOI
        inputChiSoMoi.addEventListener("input", function () {
            const chisocu = parseFloat(inputChiSoCu.value) || 0;
            const chisomoi = parseFloat(inputChiSoMoi.value) || 0;

            // Tính số dịch vụ tổng
            const sodichvuTong = Math.max(chisomoi - chisocu, 0);
            inputSoDichVuTong.value = sodichvuTong.toFixed(2);

            // Tính thành tiền dịch vụ
            const tiendichvu = sodichvuTong * parseFloat(giaDichVu);
            inputTienDichVuGhiDuoc.value = tiendichvu.toFixed(2);
        });
    } else {
        // Trạng thái lưu
        const chisomoi = inputChiSoMoi.value;
        const sodichvuTong = inputSoDichVuTong.value;
        const tiendichvuGhiDuoc = inputTienDichVuGhiDuoc.value;

        // Gửi yêu cầu cập nhật giá trị chỉ số mới vào cơ sở dữ liệu
        capNhatCoSoDuLieu(
            madichvukhucvuc,
            chisomoi,
            sodichvuTong,
            tiendichvuGhiDuoc
        )
            .then((data) => {
                if (data.success) {
                    // Cập nhật trạng thái nút khi cập nhật thành công
                    inputChiSoMoi.disabled = true;
                    button.textContent = "Chỉnh sửa";
                    button.classList.remove("btn-success");
                    button.classList.add("btn-danger");
                    button.dataset.status = "1"; // Đặt trạng thái là chỉnh sửa
                } else {
                    alert("Cập nhật thất bại");
                }
            })
            .catch((error) => {
                alert("Đã xảy ra lỗi khi cập nhật: " + error.message); // Hiển thị lỗi chi tiết
            });
    }
}

//Khau Trừ

// 1. Hàm để thu thập dữ liệu từ form
function collectFormData() {
    const form = document.getElementById("discount-form");
    return new FormData(form);
}

// 2. Hàm kiểm tra dữ liệu đã được nhập đầy đủ chưa
function validateFormData(formData) {
    // Duyệt qua các trường trong formData để kiểm tra
    let isValid = true;
    let missingFields = [];

    formData.forEach((value, key) => {
        if (!value) {
            // Nếu có trường nào chưa nhập
            missingFields.push(key);
            isValid = false;
        }
    });

    if (!isValid) {
        alert("Các trường sau chưa được nhập: " + missingFields.join(", "));
    }

    return isValid; // Trả về true nếu hợp lệ, false nếu có trường thiếu
}

// 3. Hàm để gửi yêu cầu POST đến server
function sendDiscountData(formData) {
    return fetch("/hoadon/khautru/themKhauTru/", {
        method: "POST",
        body: formData,
    }).then((response) => response.json());
}

// 4. Hàm để xử lý kết quả từ server và cập nhật giao diện
function handleSaveResponse(data) {
    if (data.success) {
        addDiscountRow(data.khautru);
    } else {
        alert("Có lỗi trong dữ liệu: " + JSON.stringify(data.errors));
    }
}

// 5. Hàm để thêm dòng mới vào bảng khấu trừ
function addDiscountRow(khautru) {
    const newRow = createDiscountRow(khautru);
    document
        .getElementById("discount-details")
        .insertAdjacentHTML("afterbegin", newRow);
}

// 6. Hàm để tạo HTML cho dòng mới trong bảng
function createDiscountRow(khautru) {
    return `
        <tr id="khautru-${khautru.MAKHAUTRU}" style="text-align: center;">
            <td>1</td>
            <td>${khautru.LOAIDIEUCHINH}</td>
            <td>${khautru.TIENKHAUTRU} đ</td>
            <td>${khautru.LYDOKHAUTRU}</td>
            <td>
                <a href="javascript:void(0);" class="btn btn-primary btn-sm"
                   style="border-radius: 20px; padding: 5px 10px; transition: all 0.3s;"
                   id="edit-${khautru.MACHISODICHVU}" data-status="1"
                   onclick="editDiscount(${khautru.MACHISODICHVU}, ${khautru.TIENKHAUTRU})">
                    <i class="fa fa-edit"></i> Chỉnh sửa
                </a>
            </td>
        </tr>
    `;
}

// 7. Hàm chính để lưu khấu trừ
function saveDiscount() {
    const formData = collectFormData();

    // Kiểm tra dữ liệu trước khi gửi lên server
    if (!validateFormData(formData)) {
        return; // Nếu có trường thiếu, dừng lại và không gửi dữ liệu
    }

    // Chuyển formData thành chuỗi để hiển thị trong alert
    let formDataValues = "";
    formData.forEach((value, key) => {
        formDataValues += `${key}: ${value}\n`; // Xây dựng chuỗi key-value
    });
    alert(formDataValues);

    // Gửi dữ liệu lên server
    sendDiscountData(formData)
        .then((data) => handleSaveResponse(data))
        .catch((error) => alert("Có lỗi xảy ra: " + error));
}

// CHỉnh sửa
function editDiscount(maKhauTru) {
    var btnText = document.getElementById("action-btn-" + maKhauTru).innerText;
    var isEditable = btnText === "Chỉnh sửa";

    // Toggle read-only status of inputs
    document.getElementById("loaidi_chinh_" + maKhauTru).disabled = !isEditable;
    document.getElementById("tienkhau_tru_" + maKhauTru).readOnly = !isEditable;
    document.getElementById("lydo_khautru_" + maKhauTru).readOnly = !isEditable;
    document.getElementById("ngay_khautru_" + maKhauTru).readOnly = !isEditable;

    if (!isEditable) {
        // If the button is "Lưu", update the data
        saveDiscountData(maKhauTru);
    } else {
        // Change button text to "Lưu" or "Chỉnh sửa"
        document.getElementById("action-btn-" + maKhauTru).innerText = "Lưu";
    }
}

function saveDiscountData(maKhauTru) {
    // Get the updated values from inputs
    const loaidi_chinh = document.getElementById(
        "loaidi_chinh_" + maKhauTru
    ).value;
    const tienkhau_tru = document.getElementById(
        "tienkhau_tru_" + maKhauTru
    ).value;
    const lydo_khautru = document.getElementById(
        "lydo_khautru_" + maKhauTru
    ).value;
    const ngay_khautru = document.getElementById(
        "ngay_khautru_" + maKhauTru
    ).value;

    // Prepare data for the request
    const data = {
        LOAIDIEUCHINH: loaidi_chinh,
        TIENKHAUTRU: tienkhau_tru,
        LYDOKHAUTRU: lydo_khautru,
        NGAYKHAUTRU: ngay_khautru,
    };

    // Send the data via fetch to update in the database
    fetch(`/hoadon/khautru/capNhatKhauTru/${maKhauTru}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": document
                .querySelector('meta[name="csrf-token"]')
                .getAttribute("content"), // Fetch CSRF token dynamically
        },
        body: JSON.stringify(data),
    })
        .then((response) => response.json())
        .then((result) => {
            if (result.success) {
                alert("Cập nhật thành công!");
                // Change button text to "Lưu" or "Chỉnh sửa"
                document.getElementById("action-btn-" + maKhauTru).innerText =
                    "Chỉnh sửa";
            } else {
                alert("Có lỗi xảy ra, vui lòng thử lại!");
            }
        })
        .catch((error) => {
            alert("Có lỗi xảy ra, vui lòng thử lại!" + error);
        });
}

//Hũy hóa đơn
function huyHoaDon(maHoaDon) {
    if (confirm("Bạn có chắc chắn muốn hủy hóa đơn này?")) {
        fetch(`/hoadon/huyHoaDon/${maHoaDon}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-TOKEN": document
                    .querySelector('meta[name="csrf-token"]')
                    .getAttribute("content"), // Fetch CSRF token dynamically
            },
        })
            .then((response) => response.json())
            .then((result) => {
                if (result.success) {
                    alert(result.message); // Hiển thị thông báo thành công
                    // Cập nhật giao diện nếu cần (ví dụ: thay đổi trạng thái)
                    location.reload(); // Tải lại trang để cập nhật trạng thái
                } else {
                    alert(result.message); // Hiển thị thông báo lỗi
                }
            })
            .catch((error) => {
                alert("Có lỗi xảy ra, vui lòng thử lại!");
            });
    }
}
// Thanh toán hóa đơn
function thanhToanHoaDon(maHoaDon) {
    if (confirm("Bạn có chắc chắn muốn thanh toán hóa đơn này?")) {
        fetch(`/hoadon/thanhToanHoaDon/${maHoaDon}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "X-CSRF-TOKEN": document
                    .querySelector('meta[name="csrf-token"]')
                    .getAttribute("content"), // Fetch CSRF token dynamically
            },
        })
            .then((response) => response.json())
            .then((result) => {
                if (result.success) {
                    alert(result.message); // Hiển thị thông báo thành công
                    // Cập nhật giao diện nếu cần (ví dụ: thay đổi trạng thái)
                    location.reload(); // Tải lại trang để cập nhật trạng thái
                } else {
                    alert(result.message); // Hiển thị thông báo lỗi
                }
            })
            .catch((error) => {
                alert("Có lỗi xảy ra, vui lòng thử lại!" + error);
            });
    }
}
