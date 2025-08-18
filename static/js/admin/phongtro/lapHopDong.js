function initHopDong() {
    // Khởi tạo các event listener cho trang lập hợp đồng
    console.log('Khởi tạo lập hợp đồng');
    
    // Xử lý sự kiện khi chọn file (nếu có upload ảnh)
    document.querySelectorAll('input[type="file"]').forEach(inputElement => {
        inputElement.addEventListener('change', function (event) {
            const file = event.target.files[0];
            const previewId = event.target.id.replace('Input', 'Preview');
            const imagePreview = document.getElementById(previewId);

            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const imgElement = document.createElement('img');
                    imgElement.src = e.target.result;
                    imgElement.style.width = '200px';
                    imgElement.style.height = '200px';
                    imgElement.style.objectFit = 'cover';

                    if (imagePreview) {
                        imagePreview.innerHTML = '';
                        imagePreview.appendChild(imgElement);
                    }
                };
                reader.readAsDataURL(file);

                const placeholder = imagePreview?.querySelector('span');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
            } else {
                alert('Vui lòng chọn một hình ảnh hợp lệ.');
                event.target.value = '';
            }
        });
    });
}
// Hàm tính ngày trả phòng
function calculateNgayTraPhong() {
    const ngayNhanPhongInput = document.getElementById('ngayNhanPhong');
    const ngayTraPhongInput = document.getElementById('ngayTraPhong');
    const thoiHanHopDongSelect = document.getElementById('thoiHanHopDong');
    
    if (!ngayNhanPhongInput || !ngayTraPhongInput || !thoiHanHopDongSelect) {
        return;
    }
    
    const ngayNhanPhong = new Date(ngayNhanPhongInput.value);
    const thoiHan = thoiHanHopDongSelect.value;

    if (!isNaN(ngayNhanPhong) && thoiHan) {
        let monthsToAdd = 1; // Mặc định là 1 tháng
        const match = thoiHan.match(/(\d+)/);
        if (match) {
            monthsToAdd = parseInt(match[1], 10);
            if (thoiHan.includes('năm')) {
                monthsToAdd *= 12; // Chuyển đổi năm sang tháng
            }
        }
        
        const endDate = new Date(ngayNhanPhong);
        endDate.setMonth(endDate.getMonth() + monthsToAdd);
        ngayTraPhongInput.value = endDate.toISOString().split('T')[0];
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
