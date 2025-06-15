function initThietLapDichVu() {
    window.loadServiceInfo = loadServiceInfo;
    window.applyService = applyService;
    window.cancelService = cancelService;
}
// Mảng lưu các dịch vụ đã chọn
var selectedServices = [];

// Tải thông tin dịch vụ từ server
function loadServiceInfo(serviceId, dichVus, MAKHUVUC) {
    try {
        // Hiển thị phần thông tin dịch vụ
        $('#service-info').show();
        // Lấy dữ liệu dịch vụ từ PHP
        var serviceData = dichVus;

        // Kiểm tra nếu serviceData không phải là mảng hợp lệ
        if (!Array.isArray(serviceData)) {
            console.error('Dữ liệu không hợp lệ: serviceData không phải là mảng.');
            return;
        }

        // Tìm dịch vụ theo ID
        var selectedService = serviceData.find(function (service) {
            return service.MADICHVU == serviceId;
        });

        if (!selectedService) {
            console.error('Không tìm thấy dịch vụ với ID:', serviceId);
            return;
        }
        // Thêm dịch vụ vào danh sách đã chọn
        selectedServices.push(serviceId);

        // Xác định số thứ tự tiếp theo (đảo ngược thứ tự)
        var nextStt = 1;
        $('#service-details tr').each(function () {
            var currentStt = parseInt($(this).find('td:first').text());
            if (!isNaN(currentStt) && currentStt >= nextStt) {
                nextStt = currentStt + 1;
            }
        });

        // Tạo thông tin dịch vụ mới
        var serviceDetails = `
                    <tr id="dichvuMOI-${selectedService.MADICHVU}">
                    <td>${nextStt}</td>
                    <td>${selectedService.TENDICHVU}</td>
                    <td>
                        <input type="number" class="form-control table-input" 
                            name="GIADICHVUMOI[${selectedService.MADICHVU}]" 
                            min="1" step="0.01" placeholder="Nhập giá">
                    </td>
                    <td>
                        <select name="KYTHANHTOANMOI[${selectedService.MADICHVU}]" class="form-select table-input"
                                id="KYTHANHTOAN-${selectedService.MADICHVU}">
                            <option value="thang">Theo tháng</option>
                            <option value="chi_so">Theo chỉ số</option>
                        </select>
                    </td>
                    <td>
                        <input type="date" name="NGAYAPDUNGMOI[${selectedService.MADICHVU}]" 
                            class="form-control table-input" placeholder="Ngày Áp Dụng">
                    </td>
                    <td>
                        <input type="date" name="NGAYHUYMOI[${selectedService.MADICHVU}]" 
                            class="form-control table-input" placeholder="Ngày Hủy">
                    </td>
                    <td>
                        <button type="button" class="btn btn-primary btn-toggle-status" 
                                onclick="applyService(${selectedService.MADICHVU}, ${MAKHUVUC})">
                            Áp Dụng
                        </button>
                    </td>
                </tr>

            `;
        // Chèn dịch vụ vào đầu bảng
        $('#service-details').prepend(serviceDetails);

        // Cập nhật lại số thứ tự của tất cả các dịch vụ sau khi thêm mới
        $('#service-details tr').each(function (index) {
            $(this).find('td:first').text(index + 1);
        });
    } catch (error) {
        console.error('Có lỗi xảy ra:', error);
    }
}

// Áp dụng dịch vụ
function applyService(serviceId, MAKHUVUC) {
    if (!MAKHUVUC) {
        alert("Không tìm thấy mã khu vực. Vui lòng kiểm tra lại.");
        return;
    }

    // Lấy giá trị từ các input
    const giaDichVuEl = document.querySelector(`input[name="GIADICHVUMOI[${serviceId}]"]`);
    const kyThanhToanEl = document.querySelector(`select[name="KYTHANHTOANMOI[${serviceId}]"]`);
    const ngayApDungEl = document.querySelector(`input[name="NGAYAPDUNGMOI[${serviceId}]"]`);
    const ngayHuyEl = document.querySelector(`input[name="NGAYHUYMOI[${serviceId}]"]`);

    const row = document.querySelector(`#dichvuMOI-${serviceId}`);

    if (!giaDichVuEl || !kyThanhToanEl || !ngayApDungEl) {
        alert("Không tìm thấy các trường dữ liệu. Vui lòng kiểm tra lại.");
        return;
    }

    const giaDichVu = giaDichVuEl.value;
    const kyThanhToan = kyThanhToanEl.value;
    const ngayApDung = ngayApDungEl.value;
    const ngayHuy = ngayHuyEl ? ngayHuyEl.value : null;

    // Kiểm tra các giá trị nhập
    if (!giaDichVu || isNaN(giaDichVu) || giaDichVu <= 0) {
        alert("Vui lòng nhập giá trị hợp lệ.");
        return;
    }
    if (!ngayApDung) {
        alert("Vui lòng chọn ngày áp dụng.");
        return;
    }
    if (ngayHuy && new Date(ngayApDung) > new Date(ngayHuy)) {
        alert("Ngày nghỉ phải sau hoặc trùng ngày áp dụng.");
        return;
    }

    // Thực hiện gửi yêu cầu
    fetch("/khuvuc/apDungDichVu/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
        },
        body: JSON.stringify({
            MADICHVU: serviceId,
            MAKHUVUC: MAKHUVUC,
            GIADICHVU: giaDichVu,
            KYTHANHTOAN: kyThanhToan,
            NGAYAPDUNG: ngayApDung,
            NGAYHUY: ngayHuy || null,
        }),
    })
        .then(response => {
            if (!response.ok) throw new Error("Mất kết nối với máy chủ");
            return response.json();
        })
        .then(data => {
            if (data.success) {
                alert(data.status || "Áp dụng thành công!");

                // Cập nhật trạng thái nút
                const button = document.querySelector(`#dichvuMOI-${serviceId} .btn-toggle-status`);
                if (button) {
                    button.textContent = "Hủy";
                    button.classList.remove("btn-primary");
                    button.classList.add("btn-danger");
                    button.setAttribute("onclick", `cancelService(${data.MADICHVUKHUVUC})`);
                    button.setAttribute("id", `button-${data.MADICHVUKHUVUC}`); // Đổi id
                    row.id = `dichvu-${data.MADICHVUKHUVUC}`; // Đổi id cho row
                }

                // Đổi tên các input
                giaDichVuEl.setAttribute('name', `GIADICHVU[${data.MADICHVUKHUVUC}]`);
                giaDichVuEl.disabled = true;
                kyThanhToanEl.setAttribute('name', `KYTHANHTOAN[${data.MADICHVUKHUVUC}]`);
                kyThanhToanEl.disabled = true;
                ngayApDungEl.setAttribute('name', `NGAYAPDUNG[${data.MADICHVUKHUVUC}]`);
                ngayApDungEl.disabled = true;
                if (ngayHuyEl) {
                    ngayHuyEl.setAttribute('name', `NGAYHUY[${data.MADICHVUKHUVUC}]`);
                    ngayHuyEl.disabled = true;
                }
            } else {
                alert(data.message || "Áp dụng thất bại.");
            }
        })
        .catch(error => {
            alert("Lỗi khi áp dụng dịch vụ: " + error.message);
        });
}


// Hủy dịch vụ
function cancelService(MADICHVUKHUVUC) {
    try {
        const currentDate = new Date();
        const formattedDate = currentDate.toISOString().slice(0, 19).replace("T", " "); // Chuyển đổi thành định dạng MySQL 'YYYY-MM-DD HH:MM:SS'
        
        const ngayHuyEl = document.querySelector(`input[name="NGAYHUY[${MADICHVUKHUVUC}]"]`);

        // Gửi yêu cầu hủy dịch vụ
        fetch(`/khuvuc/huyDichVu/${MADICHVUKHUVUC}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]').getAttribute('content'),
            },
            body: JSON.stringify({ ngayHuy: formattedDate })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Sử dụng MADICHVUKHUVUC thay vì serviceId để tìm nút button
                const button = document.querySelector(`#dichvu-${MADICHVUKHUVUC} .btn-toggle-status`);

                // Kiểm tra nếu button tồn tại
                if (button) {
                    // Xóa button khỏi DOM
                    button.remove(); // Loại bỏ button
                }

                // Cập nhật input ngày hủy với giá trị ngày hiện tại sau khi hủy thành công
                if (ngayHuyEl) {
                    ngayHuyEl.value = currentDate.toISOString().slice(0, 10); // Cập nhật chỉ ngày 'YYYY-MM-DD'
                }
            } else {
                alert(data.message || 'Hủy dịch vụ thất bại.');
            }
        })
        .catch(error => {
            console.error('Lỗi khi hủy dịch vụ:', error);
        });
    } catch (error) {
        console.error('Có lỗi xảy ra:', error);
    }
}



