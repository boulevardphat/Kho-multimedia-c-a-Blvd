import os
import math
import tkinter as tk
from tkinter import filedialog
from PIL import Image

# --- CÁC CÀI ĐẶT ---
Image.MAX_IMAGE_PIXELS = None 
DELETE_ORIGINAL = False 
TXT_FILENAME = "thong_tin_anh.txt"
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')

def get_aspect_ratio(width, height):
    if width == 0 or height == 0: return "Unknown"
    gcd = math.gcd(width, height)
    return f"{width // gcd}:{height // gcd}"

def main():
    root_tk = tk.Tk()
    root_tk.withdraw()
    
    print("👀 Đang mở cửa sổ chọn thư mục...")
    selected_dir = filedialog.askdirectory(title="Chọn thư mục chứa ảnh (sẽ quét cả thư mục con)")
    
    if not selected_dir:
        print("❌ Đã hủy thao tác.")
        return
        
    print(f"📁 Thư mục đang xử lý: {selected_dir}")
    txt_path = os.path.join(selected_dir, TXT_FILENAME)
    
    # Gom danh sách toàn bộ ảnh
    image_files = []
    for root, dirs, files in os.walk(selected_dir):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                image_files.append(os.path.join(root, file))
                
    total_images = len(image_files)
    if total_images == 0:
        print("❌ Không tìm thấy file ảnh nào!")
        return
        
    print(f"🎯 Tìm thấy {total_images} ảnh. Bắt đầu xử lý...\n")
    
    # --- TÍNH NĂNG MỚI: ĐỌC DỮ LIỆU CŨ TỪ FILE TXT (ĐỂ SKIP) ---
    processed_files = set()
    txt_exists = os.path.exists(txt_path)
    
    if txt_exists:
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Bỏ qua 2 dòng tiêu đề ban đầu
                for line in lines[2:]: 
                    parts = line.split('|')
                    if len(parts) > 0:
                        # Lấy phần tên đường dẫn (ở cột đầu tiên)
                        path_in_txt = parts[0].strip()
                        processed_files.add(path_in_txt)
            print(f"💡 Đã đọc lịch sử: Có {len(processed_files)} ảnh đã được ghi trong file TXT cũ.")
        except Exception as e:
            print(f"⚠️ Không thể đọc file txt cũ: {e}")

    count_converted = 0
    count_failed = 0
    count_skipped = 0
    
    # Mở file txt ở chế độ 'a' (append - ghi tiếp) thay vì 'w' (ghi đè)
    with open(txt_path, 'a', encoding='utf-8') as txt_file:
        if not txt_exists:
            # Nếu chưa có file txt thì mới tạo khung tiêu đề
            txt_file.write(f"{'Đường dẫn file'.ljust(60)} | {'Độ phân giải'.ljust(15)} | {'Tỷ lệ (Ratio)'}\n")
            txt_file.write("-" * 100 + "\n")
        
        # Dùng enumerate để in ra thứ tự xử lý chính xác
        for idx, file_path in enumerate(image_files, 1):
            short_path = os.path.relpath(file_path, selected_dir)
            base_name = os.path.splitext(file_path)[0]
            webp_path = f"{base_name}.webp"
            
            # --- ĐIỀU KIỆN ĐỂ BỎ QUA (SKIP) ---
            # Nếu tên ảnh đã lưu trong txt VÀ file wepb trên ổ cứng vẫn còn tồn tại
            if short_path in processed_files and os.path.exists(webp_path):
                print(f"⏩ Bỏ qua ({idx}/{total_images}): {short_path} (Đã xử lý từ trước)")
                count_skipped += 1
                continue
            
            # --- NẾU CHƯA XỬ LÝ THÌ BẮT ĐẦU CHUYỂN ĐỔI ---
            print(f"⏳ Đang xử lý ({idx}/{total_images}): {short_path}...", end=" ", flush=True)
            
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    ratio = get_aspect_ratio(width, height)
                    
                    # Xử lý an toàn ảnh vượt mốc giới hạn của WebP
                    if width > 16383 or height > 16383:
                        print(f"\n   -> [Cảnh báo] Ảnh quá to ({width}x{height}). Đang thu nhỏ...", end=" ")
                        img.thumbnail((16383, 16383), Image.Resampling.LANCZOS)
                    
                    # Convert sang hệ màu an toàn (RGB) để tránh lỗi format
                    if img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGBA') if 'A' in img.mode else img.convert('RGB')
                        
                    # Lưu file webp
                    img.save(webp_path, "webp", quality=85)
                    count_converted += 1
                    
                    # CHỈ GHI VÀO FILE TXT SAU KHI ĐÃ CHUYỂN ĐỔI THÀNH CÔNG
                    txt_file.write(f"{short_path.ljust(60)} | {f'{width}x{height}'.ljust(15)} | {ratio}\n")
                    txt_file.flush() # Ép lưu vào ổ cứng
                    os.fsync(txt_file.fileno()) 
                    
                if DELETE_ORIGINAL:
                    os.remove(file_path)
                    
                print("✅ Xong!")
                
            except Exception as e:
                count_failed += 1
                print(f"❌ LỖI: {e}")
                
    print("\n" + "="*50)
    print("📋 BẢNG TỔNG KẾT XỬ LÝ:")
    print(f"👉 Tổng số ảnh quét được : {total_images} file")
    
    if count_skipped > 0:
        print(f"⏩ Đã BỎ QUA (Skip)       : {count_skipped} file (Đã có sẵn Webp & TXT)")
        
    print(f"✅ Chuyển đổi MỚI         : {count_converted} file")
    
    if count_failed > 0:
        print(f"❌ Thất bại/Lỗi           : {count_failed} file")
        
    print(f"📄 File lưu thông tin     : {TXT_FILENAME}")
    print("="*50)

if __name__ == "__main__":
    main()