/**
 * JavaScript cho chức năng sửa khách thuê hợp đồng
 */

document.addEventListener('DOMContentLoaded', function() {
    // Xử lý radio buttons
    const tenantTypeRadios = document.querySelectorAll('input[name="tenant_type"]');
    const searchForm = document.getElementById('search_tenant_form');
    const tenantInfoForm = document.getElementById('tenant_info_form');
    const searchInput = document.getElementById('search_tenant_input');
    const searchResults = document.getElementById('search_results');
    const searchResultsList = document.getElementById('search_results_list');
    
    let searchTimeout;
    let currentSelectedTenant = null;

    // Xử lý thay đổi loại khách thuê
    tenantTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            handleTenantTypeChange();
        });
    });

    // Xử lý tìm kiếm khách thuê
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            // Clear timeout cũ
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // Ẩn kết quả nếu query quá ngắn
            if (query.length < 2) {
                hideSearchResults();
                return;
            }
            
            // Debounce search
            searchTimeout = setTimeout(() => {
                searchTenants(query);
            }, 300);
        });
    }

    function handleTenantTypeChange() {
        const selectedType = document.querySelector('input[name="tenant_type"]:checked')?.value;
        
        // Cập nhật hidden field
        document.getElementById('tenant_type_hidden').value = selectedType;
        
        switch (selectedType) {
            case 'existing':
                // Hiển thị thông tin khách thuê hiện tại
                searchForm.classList.add('hidden');
                tenantInfoForm.classList.remove('hidden');
                enableFormInputs();
                hideSearchResults();
                break;
                
            case 'search':
                // Hiển thị form tìm kiếm
                searchForm.classList.remove('hidden');
                tenantInfoForm.classList.remove('hidden');
                disableFormInputs();
                searchInput.focus();
                break;
        }
    }

    function searchTenants(query) {
        // Hiển thị loading
        showSearchLoading();
        
        fetch(`/admin/hopdong/api/tim-khach-thue/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                displaySearchResults(data.results);
            })
            .catch(error => {
                console.error('Lỗi tìm kiếm:', error);
                showSearchError('Lỗi kết nối. Vui lòng thử lại.');
            });
    }

    function displaySearchResults(results) {
        searchResultsList.innerHTML = '';
        
        if (results.length === 0) {
            searchResultsList.innerHTML = `
                <div class="px-4 py-3 text-center text-gray-500">
                    <i class="fas fa-search mr-2"></i>Không tìm thấy khách thuê nào
                </div>
            `;
        } else {
            results.forEach(tenant => {
                const item = document.createElement('div');
                item.className = 'px-4 py-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0';
                item.innerHTML = `
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="font-medium text-gray-900">${tenant.ho_ten}</div>
                            <div class="text-sm text-gray-500">
                                <i class="fas fa-phone mr-1"></i>${tenant.sdt}
                                ${tenant.email ? `<span class="ml-3"><i class="fas fa-envelope mr-1"></i>${tenant.email}</span>` : ''}
                            </div>
                        </div>
                        <div class="text-green-600">
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    </div>
                `;
                
                item.addEventListener('click', () => {
                    selectTenant(tenant);
                });
                
                searchResultsList.appendChild(item);
            });
        }
        
        showSearchResults();
    }

    function selectTenant(tenant) {
        currentSelectedTenant = tenant;
        
        // Điền thông tin vào form
        document.getElementById('MA_KHACH_THUE').value = tenant.id;
        document.getElementById('HO_TEN_KT').value = tenant.ho_ten;
        document.getElementById('SDT_KT').value = tenant.sdt;
        document.getElementById('EMAIL_KT').value = tenant.email;
        document.getElementById('GIOI_TINH_KT').value = tenant.gioi_tinh;
        document.getElementById('NGAY_SINH_KT').value = tenant.ngay_sinh;
        
        // Cập nhật search input để hiển thị khách thuê đã chọn
        searchInput.value = tenant.display_text;
        
        // Ẩn kết quả tìm kiếm
        hideSearchResults();
        
        // Enable form inputs
        enableFormInputs();
        
        // Hiệu ứng visual
        showSelectionSuccess();
    }

    function clearForm() {
        document.getElementById('HO_TEN_KT').value = '';
        document.getElementById('SDT_KT').value = '';
        document.getElementById('EMAIL_KT').value = '';
        document.getElementById('GIOI_TINH_KT').value = 'Nam';
        document.getElementById('NGAY_SINH_KT').value = '';
        searchInput.value = '';
        currentSelectedTenant = null;
    }

    function enableFormInputs() {
        const inputs = tenantInfoForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.disabled = false;
            input.classList.remove('bg-gray-100', 'cursor-not-allowed');
            input.classList.add('bg-white');
        });
    }

    function disableFormInputs() {
        const inputs = tenantInfoForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.id !== 'MA_KHACH_THUE') { // Keep hidden field enabled
                input.disabled = true;
                input.classList.remove('bg-white');
                input.classList.add('bg-gray-100', 'cursor-not-allowed');
            }
        });
    }

    function showSearchResults() {
        searchResults.classList.remove('hidden');
    }

    function hideSearchResults() {
        searchResults.classList.add('hidden');
    }

    function showSearchLoading() {
        searchResultsList.innerHTML = `
            <div class="px-4 py-3 text-center text-blue-600">
                <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mx-auto mb-2"></div>
                Đang tìm kiếm...
            </div>
        `;
        showSearchResults();
    }

    function showSearchError(message) {
        searchResultsList.innerHTML = `
            <div class="px-4 py-3 text-center text-red-600">
                <i class="fas fa-exclamation-triangle mr-2"></i>${message}
            </div>
        `;
        showSearchResults();
    }

    function showSelectionSuccess() {
        // Tạo hiệu ứng flash xanh lá cho form
        tenantInfoForm.classList.add('ring-2', 'ring-green-400');
        setTimeout(() => {
            tenantInfoForm.classList.remove('ring-2', 'ring-green-400');
        }, 1000);
    }

    // Ẩn kết quả khi click bên ngoài
    document.addEventListener('click', function(e) {
        if (!searchForm.contains(e.target)) {
            hideSearchResults();
        }
    });

    // Khởi tạo trạng thái ban đầu
    handleTenantTypeChange();
});