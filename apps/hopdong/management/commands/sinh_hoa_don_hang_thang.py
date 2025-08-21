"""
Management command để sinh hóa đơn hàng tháng tự động
Chạy bằng: python manage.py sinh_hoa_don_hang_thang --thang 12 --nam 2024
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.hopdong.services import HopDongWorkflowService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sinh hóa đơn hàng tháng cho tất cả hợp đồng đang hoạt động'

    def add_arguments(self, parser):
        parser.add_argument(
            '--thang',
            type=int,
            help='Tháng cần sinh hóa đơn (1-12), mặc định là tháng hiện tại',
        )
        
        parser.add_argument(
            '--nam',
            type=int,
            help='Năm cần sinh hóa đơn, mặc định là năm hiện tại',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chạy thử nghiệm, không thực sự tạo hóa đơn',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Bỏ qua kiểm tra hóa đơn đã tồn tại',
        )

    def handle(self, *args, **options):
        # Lấy tháng/năm từ options hoặc dùng mặc định
        today = timezone.now().date()
        thang = options['thang'] or today.month
        nam = options['nam'] or today.year
        
        # Validate tháng
        if not (1 <= thang <= 12):
            self.stdout.write(
                self.style.ERROR('Tháng phải trong khoảng 1-12')
            )
            return
        
        start_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(
                f'Bắt đầu sinh hóa đơn tháng {thang}/{nam} lúc {start_time}'
            )
        )
        
        try:
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('CHẾ ĐỘ THỬ NGHIỆM - Không tạo hóa đơn thực tế')
                )
            
            # Gọi service sinh hóa đơn
            danh_sach_hoa_don, success_msg, errors = HopDongWorkflowService.sinh_hoa_don_hang_thang_batch(
                thang=thang,
                nam=nam
            )
            
            # Hiển thị kết quả thành công
            if success_msg:
                self.stdout.write(self.style.SUCCESS(success_msg))
            
            # Hiển thị chi tiết hóa đơn được tạo
            if danh_sach_hoa_don:
                self.stdout.write(
                    self.style.SUCCESS(f"Chi tiết {len(danh_sach_hoa_don)} hóa đơn được tạo:")
                )
                for hoa_don in danh_sach_hoa_don:
                    self.stdout.write(
                        f"  - HĐ {hoa_don.MA_HOA_DON}: Phòng {hoa_don.MA_PHONG.TEN_PHONG} "
                        f"- {hoa_don.TONG_TIEN:,}đ"
                    )
            
            # Hiển thị lỗi nếu có
            if errors:
                self.stdout.write(
                    self.style.ERROR(f"Có {len(errors)} lỗi:")
                )
                for error in errors:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
            
            # Thống kê tổng kết
            tong_tien = sum(hd.TONG_TIEN for hd in danh_sach_hoa_don)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Tổng cộng: {len(danh_sach_hoa_don)} hóa đơn - {tong_tien:,}đ"
                )
            )
            
            # Thời gian hoàn thành
            end_time = timezone.now()
            duration = end_time - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f'Hoàn thành trong {duration.total_seconds():.2f} giây'
                )
            )
            
        except Exception as e:
            error_msg = f'Lỗi khi sinh hóa đơn tháng {thang}/{nam}: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(f'Command sinh_hoa_don_hang_thang failed: {error_msg}')
            raise