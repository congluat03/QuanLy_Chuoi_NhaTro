"""
Scheduler cho các tác vụ tự động hợp đồng
Sử dụng APScheduler để chạy các tác vụ theo lịch
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
import logging
import atexit

from .services import HopDongScheduleService

logger = logging.getLogger(__name__)

# Khởi tạo scheduler
scheduler = BackgroundScheduler()


def start_hop_dong_scheduler():
    """
    Khởi động scheduler cho các tác vụ hợp đồng
    """
    if scheduler.running:
        return
    
    try:
        # Tác vụ 1: Cập nhật trạng thái hợp đồng hàng ngày lúc 6:00 AM
        scheduler.add_job(
            func=cap_nhat_trang_thai_hang_ngay,
            trigger=CronTrigger(hour=6, minute=0),  # 6:00 AM hàng ngày
            id='cap_nhat_trang_thai_hop_dong',
            name='Cập nhật trạng thái hợp đồng hàng ngày',
            replace_existing=True
        )
        
        # Tác vụ 2: Sinh hóa đơn hàng tháng vào ngày 1 lúc 8:00 AM
        scheduler.add_job(
            func=sinh_hoa_don_hang_thang_tu_dong,
            trigger=CronTrigger(day=1, hour=8, minute=0),  # 8:00 AM ngày 1 hàng tháng
            id='sinh_hoa_don_hang_thang',
            name='Sinh hóa đơn hàng tháng tự động',
            replace_existing=True
        )
        
        # Tác vụ 3: Cảnh báo hợp đồng sắp hết hạn vào thứ 2 hàng tuần lúc 9:00 AM
        scheduler.add_job(
            func=canh_bao_hop_dong_sap_het_han,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),  # Thứ 2 hàng tuần
            id='canh_bao_hop_dong_sap_het_han',
            name='Cảnh báo hợp đồng sắp hết hạn',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Đã khởi động scheduler hợp đồng thành công")
        
        # Đảm bảo scheduler tắt khi ứng dụng tắt
        atexit.register(lambda: scheduler.shutdown())
        
    except Exception as e:
        logger.error(f"Lỗi khởi động scheduler hợp đồng: {str(e)}")


def stop_hop_dong_scheduler():
    """
    Dừng scheduler
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Đã dừng scheduler hợp đồng")


def cap_nhat_trang_thai_hang_ngay():
    """
    Job cập nhật trạng thái hợp đồng hàng ngày
    """
    try:
        logger.info("Bắt đầu cập nhật trạng thái hợp đồng hàng ngày")
        results = HopDongScheduleService.cap_nhat_trang_thai_hop_dong_hang_ngay()
        
        logger.info(
            f"Hoàn thành cập nhật trạng thái: "
            f"{results['sap_ket_thuc']} hợp đồng sắp kết thúc, "
            f"{results['da_het_han']} hợp đồng hết hạn"
        )
        
        if results['errors']:
            logger.warning(f"Có {len(results['errors'])} lỗi trong quá trình cập nhật")
            for error in results['errors']:
                logger.error(f"Lỗi cập nhật: {error}")
                
    except Exception as e:
        logger.error(f"Lỗi job cập nhật trạng thái hàng ngày: {str(e)}")


def sinh_hoa_don_hang_thang_tu_dong():
    """
    Job sinh hóa đơn hàng tháng tự động
    """
    try:
        logger.info("Bắt đầu sinh hóa đơn hàng tháng tự động")
        results = HopDongScheduleService.sinh_hoa_don_hang_thang_tu_dong()
        
        if results.get('so_hoa_don', 0) > 0:
            logger.info(f"Đã sinh {results['so_hoa_don']} hóa đơn hàng tháng")
        else:
            logger.info(f"Sinh hóa đơn tự động: {results.get('message', 'Không có hóa đơn nào được tạo')}")
        
        if results.get('errors'):
            logger.warning(f"Có {len(results['errors'])} lỗi trong quá trình sinh hóa đơn")
            for error in results['errors']:
                logger.error(f"Lỗi sinh hóa đơn: {error}")
                
    except Exception as e:
        logger.error(f"Lỗi job sinh hóa đơn hàng tháng: {str(e)}")


def canh_bao_hop_dong_sap_het_han():
    """
    Job cảnh báo hợp đồng sắp hết hạn
    """
    try:
        from .services import HopDongReportService
        
        logger.info("Bắt đầu kiểm tra hợp đồng sắp hết hạn")
        
        # Lấy danh sách hợp đồng sắp hết hạn trong 30 ngày
        hop_dong_sap_het_han = HopDongReportService.danh_sach_hop_dong_sap_het_han(30)
        
        if hop_dong_sap_het_han.exists():
            so_luong = hop_dong_sap_het_han.count()
            logger.warning(f"Có {so_luong} hợp đồng sắp hết hạn trong 30 ngày tới")
            
            # Log chi tiết từng hợp đồng
            for hop_dong in hop_dong_sap_het_han:
                logger.info(
                    f"HĐ {hop_dong.MA_HOP_DONG} - Phòng {hop_dong.MA_PHONG.TEN_PHONG} "
                    f"- Hết hạn: {hop_dong.NGAY_TRA_PHONG}"
                )
            
            # TODO: Gửi email/SMS thông báo cho quản lý
            # send_contract_expiry_notification(hop_dong_sap_het_han)
            
        else:
            logger.info("Không có hợp đồng nào sắp hết hạn trong 30 ngày tới")
            
    except Exception as e:
        logger.error(f"Lỗi job cảnh báo hợp đồng sắp hết hạn: {str(e)}")


# Tự động khởi động scheduler khi import module
if getattr(settings, 'AUTO_START_SCHEDULER', True):
    start_hop_dong_scheduler()


# Utility functions cho manual testing
def list_scheduled_jobs():
    """
    Liệt kê các job đã lên lịch
    """
    if not scheduler.running:
        return "Scheduler chưa được khởi động"
    
    jobs = scheduler.get_jobs()
    if not jobs:
        return "Không có job nào được lên lịch"
    
    job_info = []
    for job in jobs:
        job_info.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time,
            'trigger': str(job.trigger)
        })
    
    return job_info


def run_job_now(job_id):
    """
    Chạy một job ngay lập tức (cho testing)
    """
    if not scheduler.running:
        return "Scheduler chưa được khởi động"
    
    try:
        job = scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=None)  # Chạy ngay
            return f"Đã lên lịch chạy job '{job_id}' ngay lập tức"
        else:
            return f"Không tìm thấy job với ID: {job_id}"
    except Exception as e:
        return f"Lỗi khi chạy job: {str(e)}"