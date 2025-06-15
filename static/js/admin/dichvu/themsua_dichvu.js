function initCheckboxHandlers() {
        const selectAllCheckbox = $('#selectAllRooms');
        const roomCheckboxes = $('.room-checkbox');

        // Xử lý checkbox "Chọn tất cả"
        selectAllCheckbox.change(function() {
            roomCheckboxes.prop('checked', this.checked);
        });

        // Xử lý checkbox khu vực riêng lẻ
        roomCheckboxes.on('change', function() {
            const allChecked = roomCheckboxes.length === $('.room-checkbox:checked').length;
            selectAllCheckbox.prop('checked', allChecked);
        });
    }