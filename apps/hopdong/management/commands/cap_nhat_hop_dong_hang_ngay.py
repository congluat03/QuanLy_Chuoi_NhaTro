"""
Management command để cập nhật trạng thái hợp đồng hàng ngày
Chạy bằng: python manage.py cap_nhat_hop_dong_hang_ngay
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.hopdong.services import HopDongScheduleService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cập nhật trạng thái hợp đồng hàng ngày (sắp kết thúc, hết hạn)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Chạy thử nghiệm, không thực sự cập nhật database',
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        self.stdout.write(
            self.style.SUCCESS(f'Bắt đầu cập nhật trạng thái hợp đồng lúc {start_time}')
        )
        
        try:
            if options['dry_run']:
                self.stdout.write(
                    self.style.WARNING('CHẾ ĐỘ THỬ NGHIỆM - Không cập nhật database')
                )
            
            # Gọi service xử lý
            results = HopDongScheduleService.cap_nhat_trang_thai_hop_dong_hang_ngay()
            
            # Hiển thị kết quả
            self.stdout.write(
                self.style.SUCCESS(
                    f"Đã đánh dấu {results['sap_ket_thuc']} hợp đồng 'Sắp kết thúc'"
                )
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Đã kết thúc {results['da_het_han']} hợp đồng hết hạn"
                )
            )
            
            # Hiển thị lỗi nếu có
            if results['errors']:
                self.stdout.write(
                    self.style.ERROR(f"Có {len(results['errors'])} lỗi:")
                )
                for error in results['errors']:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
            
            # Thời gian hoàn thành
            end_time = timezone.now()
            duration = end_time - start_time
            self.stdout.write(
                self.style.SUCCESS(
                    f'Hoàn thành trong {duration.total_seconds():.2f} giây'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Lỗi khi cập nhật trạng thái hợp đồng: {str(e)}')
            )
            logger.error(f'Command cap_nhat_hop_dong_hang_ngay failed: {str(e)}')
            raise