-- ========================================
-- SQL Script để sửa lỗi Migration hopdong  
-- ========================================

-- Bước 1: Kiểm tra migration hiện tại
SELECT 'Current hopdong migrations:' as info;
SELECT app, name, applied FROM django_migrations WHERE app = 'hopdong' ORDER BY applied;

-- Bước 2: Xóa tất cả migration records của hopdong
DELETE FROM django_migrations WHERE app = 'hopdong';
SELECT ROW_COUNT() as 'Deleted migrations count';

-- Bước 3: Thêm lại migration state đúng
INSERT INTO django_migrations (app, name, applied) VALUES ('hopdong', '0001_initial', NOW());
SELECT 'Added 0001_initial migration' as info;

-- Bước 4: Kiểm tra kết quả
SELECT 'Final hopdong migrations:' as info;
SELECT app, name, applied FROM django_migrations WHERE app = 'hopdong' ORDER BY applied;

-- Bước 5: Kiểm tra tất cả apps để đảm bảo không có dependency lỗi
SELECT 'All migrations for reference:' as info;
SELECT app, COUNT(*) as migration_count FROM django_migrations GROUP BY app ORDER BY app;

-- HƯỚNG DẪN:
-- 1. Chạy toàn bộ script này trong database
-- 2. Sau đó chạy: python manage.py showmigrations hopdong
-- 3. Nếu cần: python manage.py makemigrations hopdong
-- 4. Cuối cùng: python manage.py migrate hopdong