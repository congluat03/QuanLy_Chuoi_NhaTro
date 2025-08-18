# 🗺️ Hướng dẫn cấu hình Google Maps API

## ❌ Lỗi hiện tại
```
Google Maps JavaScript API error: InvalidKeyMapError
```

Lỗi này xảy ra vì API key hiện tại không hợp lệ hoặc chưa được cấu hình đúng cách.

## 🔧 Cách khắc phục

### 1. Tạo Google Maps API Key mới

1. **Truy cập Google Cloud Console:**
   - Vào https://console.cloud.google.com/
   - Đăng nhập bằng tài khoản Google

2. **Tạo hoặc chọn Project:**
   - Tạo project mới hoặc chọn project hiện có
   - Ghi nhớ tên project

3. **Bật Google Maps JavaScript API:**
   - Vào "APIs & Services" > "Library"
   - Tìm "Maps JavaScript API"
   - Click "Enable"

4. **Tạo API Key:**
   - Vào "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy API key vừa tạo

### 2. Cấu hình API Key

1. **Hạn chế API Key (Khuyến nghị):**
   - Click vào API key vừa tạo
   - Chọn "Application restrictions" > "HTTP referrers"
   - Thêm domain của website (ví dụ: `*.yourdomain.com/*`)

2. **Cập nhật API Key trong dự án:**
   - Mở file `.env`
   - Cập nhật dòng:
   ```
   GOOGLE_MAPS_API_KEY=YOUR_NEW_API_KEY_HERE
   ```

### 3. Kiểm tra Billing

⚠️ **Quan trọng:** Google Maps API yêu cầu tài khoản có billing được kích hoạt

1. **Kích hoạt Billing:**
   - Vào "Billing" trong Google Cloud Console
   - Thêm thẻ tín dụng hoặc phương thức thanh toán
   - Google Maps có 200$ credit miễn phí mỗi tháng

## 🛠️ Fallback khi không có API Key

Nếu không thể cấu hình Google Maps API, hệ thống sẽ:

1. **Hiển thị thông báo lỗi** thân thiện
2. **Cho phép nhập tọa độ thủ công** 
3. **Vẫn có thể sử dụng nút "Mở Google Maps"** để lấy tọa độ

## 🧪 Test API Key

Sau khi cấu hình xong:

1. **Refresh trang thêm/sửa khu vực**
2. **Mở Developer Tools (F12)**
3. **Kiểm tra Console:**
   - Không có lỗi `InvalidKeyMapError`
   - Thấy message "Google Maps đã được khởi tạo thành công"

## 📞 Liên hệ hỗ trợ

Nếu vẫn gặp vấn đề:
- Kiểm tra lại domain restrictions
- Đảm bảo billing đã được kích hoạt
- Thử API key trên domain khác để test

## 💡 Mẹo

- **Để an toàn:** Hạn chế API key theo domain
- **Để tiết kiệm:** Theo dõi usage trong Google Cloud Console
- **Để backup:** Có thể tạo nhiều API key cho các môi trường khác nhau