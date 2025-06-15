function initHoaDon(hopDongDichVuList, phongTroData) {
    dateDefaul(phongTroData); // Gọi hàm thiết lập ngày tháng mặc định
    updateInvoiceDetails();
    hodonMD(hopDongDichVuList);
    envDate();
    coctro(phongTroData);
    calculateTotalServices(hopDongDichVuList);
    calculateTotal();
}

function hodonMD(hopDongDichVuList) {
    // Thêm sự kiện để tính toán mỗi khi người dùng thay đổi "Từ ngày" hoặc "Đến ngày"
    document
        .getElementById("fromDate")
        .addEventListener("change", updateInvoiceDetails);
    document
        .getElementById("toDate")
        .addEventListener("change", updateInvoiceDetails);
    document
        .getElementById("depositAmountInput")
        .addEventListener("input", (event) => {
            changeCocTro(event.target.value);
        });
    // Hóa Đơn
    $(document).ready(function () {
        $("#cancelButton").click(function () {
            $("#invoiceForm")[0].reset(); // Xóa tất cả các input trong form
        });

        // Thêm các sự kiện khác tùy chỉnh tại đây nếu cần
    });

    congTruThem();
    // Lắng nghe sự kiện input và tính toán lại
    document
        .querySelectorAll(".service-rate, .service-old, .service-new")
        .forEach(function (input) {
            input.addEventListener("input", function () {
                // Lấy dữ liệu từ backend vào JavaScript
                calculateTotalServices(hopDongDichVuList); // Tính tổng tiền cho tất cả dịch vụ
                calculateServiceTotal($(this).closest(".form-group")); // Tính tiền cho dịch vụ cụ thể
            });
        });
    // Lắng nghe sự kiện tùy chỉnh
    $("#rentAmountInput").on("valueChanged", calculateTotal);
    $("#allDepositAmountInput").on("valueChanged", calculateTotal);
    $("#totalAmountServicesInput").on("valueChanged", calculateTotal);
    $("#deductionAmountInput").on("valueChanged", calculateTotal);
}

function envDate() {
    // Thêm sự kiện cho các trường ngày tháng
    const dueDateInput = document.getElementById("dueDate");
    const monthInput = document.getElementById("month");
    const invoiceDateInput = document.getElementById("invoiceDate");

    const today = new Date(); // Đảm bảo biến today được khai báo

    dueDateInput.addEventListener("change", function () {
        if (new Date(dueDateInput.value) <= new Date(invoiceDateInput.value)) {
            alert("Hạn đóng tiền phải lớn hơn Ngày lập hóa đơn!");
            dueDateInput.value = ""; // Reset lại giá trị
        }
    });

    monthInput.addEventListener("change", function () {
        const selectedMonth = new Date(monthInput.value + "-01");
        if (selectedMonth > today) {
            alert("Tháng lập phiếu không được lớn hơn tháng hiện tại!");
            monthInput.value = today.toISOString().slice(0, 7); // Thiết lập lại giá trị
        }
    });
}
// Hàm thiết lập ngày tháng mặc định
function dateDefaul(phongTroData) {
    const today = new Date(); // Ngày hiện tại

    // Thiết lập giá trị mặc định cho "Ngày lập hóa đơn"
    const invoiceDateInput = document.getElementById("invoiceDate");
    invoiceDateInput.value = today.toISOString().split("T")[0];

    // Thiết lập giá trị mặc định cho "Tháng lập phiếu"
    const monthInput = document.getElementById("month");
    monthInput.value = today.toISOString().slice(0, 7); // Lấy năm-tháng

    // Thiết lập giá trị mặc định cho "Hạn đóng tiền"
    const dueDateInput = document.getElementById("dueDate");
    const dueDate = new Date(today); // Sao chép ngày hiện tại
    dueDate.setDate(today.getDate() + 7); // Thêm 7 ngày
    dueDateInput.value = dueDate.toISOString().split("T")[0];

    // Kiểm tra và thiết lập "Từ ngày" từ phongTroData
    if (phongTroData && phongTroData.NGAYNHANPHONG) {
        const fromDate = new Date(phongTroData.NGAYNHANPHONG); // Chuyển ngày sang đối tượng Date
        document.getElementById("fromDate").value = fromDate
            .toISOString()
            .split("T")[0]; // Chuyển về định dạng YYYY-MM-DD

        // Thiết lập "Đến ngày" là 1 tháng sau từ ngày "Từ ngày"
        const nextMonthSameDay = new Date(fromDate); // Lấy ngày "Từ ngày"
        nextMonthSameDay.setMonth(fromDate.getMonth() + 1); // Tăng tháng lên 1
        const toDate = nextMonthSameDay.toISOString().split("T")[0]; // Chuyển đổi ngày sang định dạng YYYY-MM-DD
        document.getElementById("toDate").value = toDate;
    }
}
// Hàm tính số ngày giữa 2 ngày
function calculateDays(fromDate, toDate) {
    const from = new Date(fromDate);
    const to = new Date(toDate);
    const timeDiff = to.getTime() - from.getTime();
    return Math.ceil(timeDiff / (1000 * 3600 * 24)); // Convert milliseconds to days
}

// Hàm tính số tháng và số ngày
function calculateMonthsAndDays(fromDate, toDate) {
    const from = new Date(fromDate);
    const to = new Date(toDate);

    let months =
        to.getMonth() -
        from.getMonth() +
        12 * (to.getFullYear() - from.getFullYear());
    if (to.getDate() < from.getDate()) {
        months--; // Nếu ngày đến nhỏ hơn ngày từ, giảm tháng
    }

    // Tính số ngày còn lại trong tháng sau khi đã trừ số tháng
    let days = calculateDays(fromDate, toDate) - months * 30; // Lấy số ngày còn lại sau khi trừ đi số tháng

    return {
        months,
        days,
    };
}

// Hàm tính số tiền
function calculateDays(fromDate, toDate) {
    const from = new Date(fromDate); // Đảm bảo từ ngày là đối tượng Date
    const to = new Date(toDate); // Đảm bảo đến ngày là đối tượng Date
    const timeDiff = to.getTime() - from.getTime();
    return Math.ceil(timeDiff / (1000 * 3600 * 24)); // Chuyển đổi từ mili giây sang ngày
}

// Hàm tính số tiền
function calculateAmount(fromDate, toDate) {
    try {
        // Kiểm tra xem ngày nhập vào có hợp lệ không
        if (!fromDate || !toDate) {
            throw new Error("Ngày nhập không hợp lệ.");
        }

        // Đảm bảo fromDate và toDate là đối tượng Date hợp lệ
        const from = new Date(fromDate);
        const to = new Date(toDate);

        if (isNaN(from) || isNaN(to)) {
            throw new Error("Ngày nhập không hợp lệ.");
        }
        // Tính số ngày giữa từ ngày và đến ngày
        const totalDays = calculateDays(from, to);
        // Kiểm tra nếu số ngày không hợp lệ
        if (totalDays <= 0) {
            throw new Error(
                "Số ngày tính không hợp lệ. Ngày đến phải sau ngày từ."
            );
        }

        // Lấy ngày của tháng tiếp theo từ ngày "fromDate"
        const nextMonthSameDay = new Date(from); // Tạo bản sao mới của fromDate
        nextMonthSameDay.setMonth(from.getMonth() + 1); // Tăng tháng lên 1

        // Tính số ngày của tháng tiếp theo từ "fromDate"
        const totalDaysNextMonth = calculateDays(from, nextMonthSameDay);

        // Kiểm tra nếu số ngày của tháng tiếp theo không hợp lệ
        if (totalDaysNextMonth <= 0) {
            throw new Error("Ngày của tháng tiếp theo không hợp lệ.");
        }

        // Giả sử giá tiền mỗi ngày là 3.000.000 VND cho tháng sau
        const dailyRate = 3000000 / totalDaysNextMonth; // Tính giá tiền mỗi ngày

        // Tính số tiền phải trả
        return dailyRate * totalDays;
    } catch (error) {
        // Hiển thị thông báo lỗi
        alert("Lỗi: " + error.message);
        console.error(error);
        return null; // Trả về null nếu có lỗi
    }
}

// Hàm cập nhật thông tin
function updateInvoiceDetails() {
    const fromDate = document.getElementById("fromDate").value;
    const toDate = document.getElementById("toDate").value;

    // Nếu người dùng đã chọn cả "Từ ngày" và "Đến ngày"
    if (fromDate && toDate) {
        // Tính toán số tháng và số ngày
        const { months, days } = calculateMonthsAndDays(fromDate, toDate);

        // Cập nhật số tháng và số ngày
        document.getElementById(
            "monthDays"
        ).textContent = `${months} tháng, ${days} ngày`;

        // Tính tiền và cập nhật
        const totalAmount = calculateAmount(fromDate, toDate);

        // Cập nhật thành tiền (Giả sử giảm giá 600000 đ)
        $("#finalAmount").val(totalAmount); // Định dạng tiền tệ

        setHiddenValue("#rentAmountInput", totalAmount); // Ví dụ
        // Định dạng tiền tệ theo kiểu Việt Nam (dấu chấm phân cách ngàn)
        document.getElementById(
            "totalAmount"
        ).textContent = `${totalAmount.toLocaleString("vi-VN")} đ`;

        // Hiển thị giá trị tiền thuê với định dạng đúng
        document.getElementById(
            "rentAmount"
        ).textContent = `${totalAmount.toLocaleString("vi-VN")} đ`;
    }
}

function coctro(phongTroData) {
    // Lấy số tiền cọc từ dữ liệu
    let tienco = phongTroData.SOTIENCOC || 0; // Giá trị mặc định là 0 nếu không có
    changeCocTro(tienco);
    tienco = Number(tienco);
    // Cập nhật giá trị vào input (hiển thị dưới dạng số thực, không có dấu phân cách ngàn)
    document.getElementById("depositAmountInput").value = tienco;
}

function changeCocTro(tienco) {
    tienco = Number(tienco);
    setHiddenValue("#allDepositAmountInput", tienco); // Ví dụ

    // Định dạng số theo kiểu Việt Nam (thêm dấu chấm phân cách ngàn)
    const formattedAmount = tienco.toLocaleString("vi-VN");

    // Cập nhật giá trị định dạng vào phần tử hiển thị
    document.getElementById(
        "depositAmount"
    ).textContent = `${formattedAmount} đ`;
    document.getElementById(
        "depositAmounttotle"
    ).textContent = `${formattedAmount} đ`;
}

// Hàm tính tổng tiền tất cả dịch vụ
function calculateTotalServices(hopDongDichVuList) {
    let totalAmount = 0;
    // In cấu trúc JSON ra console để dễ dàng debug

    // Lặp qua tất cả các dịch vụ trong hopDongDichVuList
    hopDongDichVuList.forEach((item) => {
        // Kiểm tra và lấy các input dựa trên tên dịch vụ
        const serviceName = item.dich_vu.TENDICHVU
            ? item.dich_vu.TENDICHVU.replace(/\s+/g, "_").toLowerCase()
            : "service";

        // Lấy các input sử dụng jQuery
        const rateInput = $("#" + serviceName + "Rate");
        const oldInput = $("#" + serviceName + "Old");
        const newInput = $("#" + serviceName + "New");

        // Nếu không tìm thấy input, tiếp tục vòng lặp
        if (
            rateInput.length === 0 ||
            oldInput.length === 0 ||
            newInput.length === 0
        ) {
            console.warn(
                "Missing inputs for service: " + item.dich_vu.TENDICHVU
            );
            return;
        }

        // Lấy giá trị từ các input, nếu không có thì mặc định là 0
        const rate = parseFloat(rateInput.val()) || 0;
        const old = parseFloat(oldInput.val()) || 0;
        const newVal = parseFloat(newInput.val()) || 0;

        // Tính số tiền của dịch vụ này: rate * (new - old)
        const serviceAmount = rate * (newVal - old);

        // Cộng dồn tổng tiền dịch vụ
        totalAmount += serviceAmount;
    });
    // Hiển thị tổng tiền dịch vụ (định dạng theo VND)
    setHiddenValue("#totalAmountServicesInput", totalAmount); // Ví dụ
    document.getElementById(
        "totalAmountServices"
    ).textContent = `${totalAmount.toLocaleString("vi-VN")} đ`;
}
// Hàm tính lại tiền dịch vụ cho dịch vụ cụ thể
function calculateServiceTotal(formGroup) {
    var rate = parseFloat(formGroup.find(".service-rate").val()) || 0;
    var old = parseFloat(formGroup.find(".service-old").val()) || 0;
    var newAmount = parseFloat(formGroup.find(".service-new").val()) || 0;

    // Tính tiền dịch vụ: (số mới - số cũ) * đơn giá
    var serviceTotal = (newAmount - old) * rate;

    // Cập nhật giá trị Tiền dịch vụ vào input ẩn
    formGroup.find(".service-total").val(serviceTotal.toFixed(2));

    // Nếu cần thiết, bạn có thể làm gì đó với tiền dịch vụ tính toán được, ví dụ như hiển thị nó.
    console.log("Tiền dịch vụ:", serviceTotal.toFixed(2));
}

function congTruThem() {
    let adjustmentCount = 0; // Biến đếm số form đã thêm

    // Thêm một form mới khi nhấn nút "Thêm Cộng thêm / Giảm trừ"
    document
        .getElementById("addAdjustmentBtn")
        .addEventListener("click", function () {
            const adjustmentContainer = document.getElementById(
                "adjustmentContainer"
            );
            adjustmentCount++;

            // Tạo HTML cho một form điều chỉnh mới
            const newAdjustmentForm = `
                <div class="adjustment-item" id="adjustmentItem${adjustmentCount}">
                    <div class="input-group">
                        <span class="input-group-addon">Loại điều chỉnh</span>
                        <div class="radio-group" style="margin-left: 15px">
                            <label>
                                <input type="radio" name="adjustments[${adjustmentCount}][type]" value="Cộng" checked> Cộng [+]
                            </label>
                            <label>
                                <input type="radio" name="adjustments[${adjustmentCount}][type]" value="Trừ"> Giảm [-]
                            </label>
                        </div>
                    </div>
                    <div class="input-group">
                        <span class="input-group-addon">Số tiền (đ)</span>
                        <input type="number" class="form-control adjustment-amount" name="adjustments[${adjustmentCount}][amount]" placeholder="Nhập số tiền" value="">
                    </div>
                    <div class="input-group">
                        <span class="input-group-addon">Lý do</span>
                        <textarea class="form-control adjustment-reason" name="adjustments[${adjustmentCount}][reason]" placeholder="Nhập lý do" rows="3"></textarea>
                    </div>
                    <button type="button" class="btn btn-danger mt-2 removeAdjustmentBtn" data-id="adjustmentItem${adjustmentCount}">
                        Xóa
                    </button>
                    <hr>
                </div>
            `;

            // Thêm form vào container
            adjustmentContainer.insertAdjacentHTML(
                "beforeend",
                newAdjustmentForm
            );
            calculateAdjustmentTotal();
        });

    // Xóa một form điều chỉnh
    document
        .getElementById("adjustmentContainer")
        .addEventListener("click", function (event) {
            if (event.target.classList.contains("removeAdjustmentBtn")) {
                const formId = event.target.getAttribute("data-id");
                const formElement = document.getElementById(formId);
                if (formElement) {
                    formElement.remove();
                }
                calculateAdjustmentTotal();
            }
        });

    // Tính tổng số tiền sau khi cộng hoặc trừ
    calculateAdjustmentTotal();

    // Gọi hàm tính tổng khi có sự thay đổi hoặc khi người dùng thay đổi số tiền
    document
        .getElementById("adjustmentContainer")
        .addEventListener("input", calculateAdjustmentTotal);
}

// Tính tổng số tiền sau khi cộng hoặc trừ
function calculateAdjustmentTotal() {
    let totalAmount = 0;

    // Lặp qua tất cả các form để tính toán tổng tiền
    const adjustmentItems = document.querySelectorAll(".adjustment-item");
    adjustmentItems.forEach((item) => {
        const adjustmentType = item.querySelector(
            'input[name^="adjustments"][name$="[type]"]:checked'
        ).value; // Cộng hoặc trừ
        const amount =
            parseFloat(item.querySelector(".adjustment-amount").value) || 0; // Số tiền
        const reason = item.querySelector(".adjustment-reason").value; // Lý do

        if (adjustmentType === "Cộng") {
            totalAmount += amount; // Cộng thêm
        } else if (adjustmentType === "Trừ") {
            totalAmount -= amount; // Giảm trừ
        }
    });
    setHiddenValue("#deductionAmountInput", totalAmount); // Ví dụ
    // Hiển thị tổng số tiền sau khi tính toán
    document.getElementById("deductionAmount").innerText =
        totalAmount.toLocaleString("vi-VN") + " đ"; // Hiển thị tổng tiền
    document.getElementById("totalAmountDisplay").innerText =
        totalAmount.toLocaleString("vi-VN") + " đ"; // Hiển thị tổng tiền
}

function calculateTotal() {
    // Lấy các giá trị từ các input ẩn và kiểm tra tính hợp lệ của chúng
    var rentAmount =
        parseFloat(document.getElementById("rentAmountInput").value) || 0;
    var depositAmount =
        parseFloat(document.getElementById("allDepositAmountInput").value) || 0;
    var totalAmountServices =
        parseFloat(document.getElementById("totalAmountServicesInput").value) ||
        0;
    var deductionAmount =
        parseFloat(document.getElementById("deductionAmountInput").value) || 0;
    // Tính tổng tiền
    var totalAmount =
        rentAmount + depositAmount + totalAmountServices + deductionAmount;

    // Cập nhật lại các giá trị hiển thị
    document.getElementById("allTotalAmountInput").value = totalAmount;
    document.getElementById(
        "allTotalAmount"
    ).innerText = `${totalAmount.toLocaleString("vi-VN")} đ`;
}

//hàm sử lý tahi đọi dự liệu
function setHiddenValue(selector, value) {
    $(selector).val(value); // Cập nhật giá trị
    $(selector).trigger("valueChanged"); // Kích hoạt sự kiện tùy chỉnh
}
