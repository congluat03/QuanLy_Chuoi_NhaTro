import google.generativeai as genai
from django.conf import settings
import json


class GeminiChatService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
    
    def get_response(self, user_message, conversation_history=None):
        """
        Gửi tin nhắn đến Gemini AI và nhận phản hồi
        """
        if not self.model:
            return {
                'success': False,
                'message': 'Dịch vụ AI chưa được cấu hình. Vui lòng liên hệ quản trị viên.',
                'error': 'API key not configured'
            }
        
        try:
            # Chuẩn bị prompt với context về website quản lý nhà trọ
            system_context = """
            Bạn là trợ lý AI thông minh cho website Quản lý Nhà Trọ.
            
            Website này hỗ trợ:
            - Tìm phòng trọ
            - Đặt phòng trọ
            - Quản lý hợp đồng thuê
            - Xem hóa đơn hàng tháng
            - Tra cứu thông tin đặt phòng
            - Cập nhật thông tin cá nhân
            
            Hãy trả lời một cách thân thiện, hữu ích và chính xác. 
            Nếu câu hỏi không liên quan đến dịch vụ của website, 
            hãy lịch sự chuyển hướng người dùng về các chức năng chính.
            
            Sử dụng tiếng Việt để trả lời.
            """
            
            # Tạo prompt đầy đủ
            full_prompt = f"{system_context}\n\nNgười dùng hỏi: {user_message}"
            
            # Nếu có lịch sử hội thoại, thêm vào context
            if conversation_history:
                history_text = "\n\nLịch sử hội thoại:\n"
                for msg in conversation_history[-5:]:  # Chỉ lấy 5 tin nhắn gần nhất
                    history_text += f"Người dùng: {msg.get('user', '')}\nAI: {msg.get('ai', '')}\n"
                full_prompt = system_context + history_text + f"\n\nNgười dùng hỏi: {user_message}"
            
            # Gửi request tới Gemini
            response = self.model.generate_content(full_prompt)
            
            return {
                'success': True,
                'message': response.text,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng thử lại sau.',
                'error': str(e)
            }
    
    def is_available(self):
        """
        Kiểm tra xem dịch vụ Gemini có sẵn sàng không
        """
        return self.model is not None and bool(self.api_key)