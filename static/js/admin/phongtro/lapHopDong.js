function initHopDong() {
    // NHẠP CHỈ SỐ DỊCH VỤ MỚI
    document.querySelectorAll('.select-cach-tinh').forEach(select => {
        select.addEventListener('change', function () {
            const serviceId = this.getAttribute('data-id');
            const chiSoInput = document.getElementById(`chi-so-${serviceId}`);
            if (this.value === 'thang') {
                chiSoInput.disabled = true;
                chiSoInput.value = '';
            } else {
                chiSoInput.disabled = false;
            }
        });
    });
    
    const data = {
        "Hà Nội": {
            "Quận/Huyện": {
                "Hoàn Kiếm": ["Phường Hàng Bạc", "Phường Hàng Đào", "Phường Cửa Nam", "Phường Lý Thái Tổ"],
                "Đống Đa": ["Phường Phương Mai", "Phường Khâm Thiên", "Phường Thổ Quan", "Phường Quang Trung"],
                "Ba Đình": ["Phường Điện Biên", "Phường Ba Đình", "Phường Kim Mã", "Phường Cống Vị"],
                "Hai Bà Trưng": ["Phường Thanh Nhàn", "Phường Bạch Mai", "Phường Lê Đại Hành", "Phường Quỳnh Mai"],
                "Cầu Giấy": ["Phường Dịch Vọng Hậu", "Phường Yên Hòa", "Phường Mai Dịch", "Phường Dịch Vọng"],
                "Long Biên": ["Phường Gia Thụy", "Phường Bồ Đề", "Phường Ngọc Lâm", "Phường Cự Khối"],
                "Tây Hồ": ["Phường Phú Thượng", "Phường Nhật Tân", "Phường Quảng An", "Phường Thụy Khuê"],
                "Thanh Xuân": ["Phường Nhân Chính", "Phường Thanh Xuân Bắc", "Phường Thanh Xuân Nam", "Phường Hạ Đình"]
            }
        },
        "Hồ Chí Minh": {
            "Quận/Huyện": {
                "Quận 1": ["Phường Bến Nghé", "Phường Bến Thành", "Phường Cầu Ông Lãnh", "Phường Nguyễn Thái Bình", "Phường Phạm Ngũ Lão", "Phường Tân Định", "Phường Cô Giang", "Phường Đa Kao"],
                "Quận 2": ["Phường An Khánh", "Phường An Lợi Đông", "Phường Bình An", "Phường Thạnh Mỹ Lợi"],
                "Quận 3": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6"],
                "Quận 10": ["Phường 10", "Phường 11", "Phường 12", "Phường 13"],
                "Bình Thạnh": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5", "Phường 6", "Phường 7"],
                "Tân Bình": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5"],
                "Gò Vấp": ["Phường 1", "Phường 2", "Phường 3", "Phường 4", "Phường 5"],
                "Phú Nhuận": ["Phường 1", "Phường 2", "Phường 3", "Phường 4"]
            }
        },
        "Cần Thơ": {
            "Quận/Huyện": {
                "Ninh Kiều": ["Phường An Cư", "Phường Cái Khế", "Phường Hưng Lợi", "Phường Thới Bình", "Phường Tân An"],
                "Bình Thủy": ["Phường Bùi Hữu Nghĩa", "Phường Trà Nóc", "Phường Thới An Đông", "Phường An Thới"],
                "Cái Răng": ["Phường Ba Láng", "Phường Phú Thứ", "Phường Hưng Phú", "Phường Thới Hòa"],
                "Ô Môn": ["Phường Thới An", "Phường Long Hòa", "Phường Phước Thới", "Phường Lê Bình"],
                "Vĩnh Thạnh": ["Xã Vĩnh Thạnh", "Xã Thạnh An", "Xã Bình Thành", "Xã Thới Hòa", "Xã Trường Thắng"],
                "Phong Điền": ["Xã Phong Điền", "Xã Nhơn Ái", "Xã Giai Xuân", "Xã Trường Long", "Xã Đông Bình"]
            }
        },
        "Đà Nẵng": {
            "Quận/Huyện": {
                "Hải Châu": ["Phường Phước Ninh", "Phường Hòa Thuận Tây", "Phường Bình Hiên", "Phường Thanh Bình"],
                "Ngũ Hành Sơn": ["Phường Mỹ An", "Phường Khuê Mỹ", "Phường Hòa Hải", "Phường Hòa Quý"],
                "Liên Chiểu": ["Phường Hòa Minh", "Phường Lệ Thủy", "Phường Thủy Dương", "Phường Hòa Bắc"],
                "Cẩm Lệ": ["Phường Hòa Thọ Đông", "Phường Hòa Thọ Tây", "Phường Cẩm An", "Phường Cẩm Trung"]
            }
        },
        "Hải Phòng": {
            "Quận/Huyện": {
                "Ngô Quyền": ["Phường Máy Tơ", "Phường Cầu Đất", "Phường Lê Chân", "Phường Vạn Mỹ"],
                "Lê Chân": ["Phường Trại Cau", "Phường Dư Hàng Kênh", "Phường Cầu Tre", "Phường Lạch Tray"],
                "Kiến An": ["Phường Bắc Sơn", "Phường Đồng Quốc Bình", "Phường Quán Trữ", "Phường Tràng Cát"]
            }
        }
    };

    // Hàm cập nhật Quận/Huyện dựa trên tỉnh thành được chọn
    document.getElementById("tinh-thanh-pho").addEventListener("change", function () {
        const tinhThanhPho = this.value;
        const quanHuyenSelect = document.getElementById("quan-huyen");
        const phuongXaSelect = document.getElementById("phuong-xa");

        // Xóa các tùy chọn Quận/Huyện cũ
        quanHuyenSelect.innerHTML = '<option value="">Chọn Quận/Huyện</option>';
        phuongXaSelect.innerHTML = '<option value="">Chọn Phường/Xã</option>';

        if (tinhThanhPho && data[tinhThanhPho]) {
            // Lấy danh sách Quận/Huyện tương ứng với Tỉnh/Thành phố
            const quanHuyenData = data[tinhThanhPho]["Quận/Huyện"];
            for (const quanHuyen in quanHuyenData) {
                const option = document.createElement("option");
                option.value = quanHuyen;
                option.textContent = quanHuyen;
                quanHuyenSelect.appendChild(option);
            }
        }
    });

    // Hàm cập nhật Phường/Xã dựa trên Quận/Huyện được chọn
    document.getElementById("quan-huyen").addEventListener("change", function () {
        const quanHuyen = this.value;
        const tinhThanhPho = document.getElementById("tinh-thanh-pho").value;
        const phuongXaSelect = document.getElementById("phuong-xa");

        // Xóa các tùy chọn Phường/Xã cũ
        phuongXaSelect.innerHTML = '<option value="">Chọn Phường/Xã</option>';

        if (tinhThanhPho && quanHuyen && data[tinhThanhPho]) {
            // Lấy danh sách Phường/Xã cho Quận/Huyện đã chọn
            const phuongXaData = data[tinhThanhPho]["Quận/Huyện"][quanHuyen];
            phuongXaData.forEach(phuongXa => {
                const option = document.createElement("option");
                option.value = phuongXa;
                option.textContent = phuongXa;
                phuongXaSelect.appendChild(option);
            });
        }
    });

    // Xử lý sự kiện khi chọn file
    document.querySelectorAll('input[type="file"]').forEach(inputElement => {

        inputElement.addEventListener('change', function (event) {
            const file = event.target.files[0]; // Lấy file đầu tiên trong danh sách file đã chọn
            const previewId = event.target.id.replace('Input', 'Preview'); // Xác định ID khung preview tương ứng
            const imagePreview = document.getElementById(previewId);

            // Kiểm tra nếu file là hình ảnh
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    // Tạo phần tử hình ảnh và hiển thị
                    const imgElement = document.createElement('img');
                    imgElement.src = e.target.result;

                    // Thiết lập kích thước cố định cho hình ảnh
                    imgElement.style.width = '200px'; // Đặt chiều rộng cố định
                    imgElement.style.height = '200px'; // Đặt chiều cao cố định
                    imgElement.style.objectFit = 'cover'; // Đảm bảo ảnh không bị méo

                    // Xóa nội dung trước đó và thêm hình ảnh vào khung
                    imagePreview.innerHTML = ''; // Xóa nội dung cũ
                    imagePreview.appendChild(imgElement);
                };
                reader.readAsDataURL(file);

                // Ẩn thông báo "Chưa có hình ảnh" nếu có
                const placeholder = imagePreview.querySelector('span');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
            } else {
                // Nếu không phải là hình ảnh, hiển thị thông báo lỗi
                alert('Vui lòng chọn một hình ảnh hợp lệ.');
                // Reset input nếu không hợp lệ
                event.target.value = '';
            }
        });
    });

    document.getElementById("show-more").addEventListener("click", function () {
        var detailForm1 = document.getElementById("detailForm1");
        var detailForm2 = document.getElementById("detailForm2");
        var detailForm3 = document.getElementById("detailForm3");

        if (detailForm1.style.display === "none" || detailForm1.style.display === "") {
            detailForm1.style.display = "block";
        } else {
            detailForm1.style.display = "none";
        }
        if (detailForm2.style.display === "none" || detailForm2.style.display === "") {
            detailForm2.style.display = "block";
        } else {
            detailForm2.style.display = "none";
        }
        if (detailForm3.style.display === "none" || detailForm3.style.display === "") {
            detailForm3.style.display = "block";
        } else {
            detailForm3.style.display = "none";
        }
    });

    // các móc thời gian 
    const ngayNhanPhongInput = document.getElementById('NGAYNHANPHONG');
    const ngayTraPhongInput = document.getElementById('NGAYTRAPHONG');
    const thoiHanHopDongSelect = document.getElementById('THOIHANHOPDONG');
    calculateNgayTraPhong();

    // Khi thay đổi ngày nhận phòng
    ngayNhanPhongInput.addEventListener('change', calculateNgayTraPhong);

    // Khi thay đổi thời hạn hợp đồng
    thoiHanHopDongSelect.addEventListener('change', calculateNgayTraPhong);
    
    // Thêm sự kiện chuyển đổi trạng thái
    document.querySelectorAll('.btn-toggle-status').forEach(function (button) {
        button.addEventListener('click', function () {
            const dichVuId = this.getAttribute('data-id');
            const inputHidden = document.getElementById(`trangthaiapdung-${dichVuId}`);
            const currentStatus = this.getAttribute('data-status');

            // Chuyển đổi trạng thái
            if (currentStatus === "Hủy") {
                this.textContent = "Hủy";
                this.classList.remove('btn-primary');
                this.classList.add('btn-danger');
                this.setAttribute('data-status', "Áp Dụng");
                inputHidden.value = "Áp Dụng";
            } else {
                this.textContent = "Áp Dụng";
                this.classList.remove('btn-danger');
                this.classList.add('btn-primary');
                this.setAttribute('data-status', "Hủy");
                inputHidden.value = "Hủy";
            }
        });
    });
}
// Hàm tính ngày trả phòng
function calculateNgayTraPhong() {
    const ngayNhanPhongInput = document.getElementById('NGAYNHANPHONG');
    const ngayTraPhongInput = document.getElementById('NGAYTRAPHONG');
    const thoiHanHopDongSelect = document.getElementById('THOIHANHOPDONG');
    const ngayNhanPhong = new Date(ngayNhanPhongInput.value);
    const thoiHan = thoiHanHopDongSelect.value;

    if (!isNaN(ngayNhanPhong)) {
        let monthsToAdd = 1; // Mặc định là 1 tháng
        if (thoiHan) {
            const match = thoiHan.match(/(\d+)/);
            if (match) {
                monthsToAdd = parseInt(match[1], 10);
                if (thoiHan.includes('năm')) {
                    monthsToAdd *= 12; // Chuyển đổi năm sang tháng
                }
            }
        }
        ngayNhanPhong.setMonth(ngayNhanPhong.getMonth() + monthsToAdd);
        ngayTraPhongInput.value = ngayNhanPhong.toISOString().split('T')[0];
    }
}

function changeTab(targetId) {
    const allTabs = document.querySelectorAll('.tab-pane');
    allTabs.forEach(tab => {
        tab.classList.remove('active', 'in');
        tab.classList.add('fade');
    });

    const targetTab = document.querySelector(targetId);
    if (targetTab) {
        targetTab.classList.add('active', 'in');
        targetTab.classList.remove('fade');
    }

    const allTabLinks = document.querySelectorAll('#myTabedu1 li');
    allTabLinks.forEach(tab => {
        tab.classList.remove('active');
    });

    const targetTabLink = document.querySelector(`#myTabedu1 a[href="${targetId}"]`);
    if (targetTabLink) {
        targetTabLink.parentElement.classList.add('active');
    }
}
