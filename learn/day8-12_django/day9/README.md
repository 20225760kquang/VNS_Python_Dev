# Django REST Framework Inventory API (Day 9)


## Các Thay Đổi Về Mặt Kỹ Thuật (So với Day 8)
* **Loại bỏ HTML/UI**: Các Views render ra giao diện Bootstrap (`dashboard.html`) bị xóa bỏ để trả về ròng cấu trúc **JSON** (Backend-only).
* **Serializers**: Cấu hình `ModelSerializer` chuyển đổi cấu trúc Model thành chuẩn JSON. Tích hợp `SerializerMethodField` để tính toán logic (`is_low_stock`), hay hiển thị chi tiết Model liên kết (nested serializer).
* **ViewSets & Generic Views**: Áp dụng `ModelViewSet` gom chung logic của CRUD (Create, Retrieve, Update, Delete) vào trong 1 class duy nhất cho từng đối tượng.
* **Router Mặc Định**: Thay vì viết riêng lẻ từng function path, url được mapping tự động cấp tốc nhờ `DefaultRouter` của DRF.
* **Authentication**: Toàn bộ hệ thống API được đưa vào diện bảo mật, cấu hình quyền `IsAuthenticated` (xác thực bằng Basic Auth hoặc Session Auth).

---

## Kiến Trúc Các Bảng (Models)

1. **Category (Danh mục)**: Lưu phân loại danh mục hàng hóa (Điện tử, Nội thất...).
2. **Supplier (Nhà cung cấp)**: Thông tin đối tác cung ứng gồm tên, số điện thoại, email và địa chỉ.
3. **Product (Sản phẩm)**: Bảng quan trọng nhất, chứa SKU, giá nhập (`unit_price`), số lượng tồn kho hiện tại (`stock_quantity`) và định mức an toàn (`reorder_level`). Có khóa ngoại trỏ tới `Category` và `Supplier`.
4. **StockTransaction (Giao dịch Kho)**: Lịch sử theo dõi các lần nhập mới (IN) hay xuất kho bán (OUT). Mỗi record lưu lại số thay đổi và thời điểm thao tác đối với từng `Product`.

---

## API Endpoints
Toàn bộ các URL dưới đây được lấy gốc từ `http://127.0.0.1:8000/`. (Có hỗ trợ các phương thức GET, POST, PUT, PATCH, DELETE tùy theo ViewSet).

* `/api/inventory/categories/` : Quản lý Danh mục.
* `/api/inventory/suppliers/` : Quản lý Đối tác cung cấp.
* `/api/inventory/transactions/` : Giao dịch biến động nhập xuất kho.
* `/api/inventory/products/` : Danh sách/Thêm bớt sản phẩm (Trả về cả thông tin `total_value` và `is_low_stock` custom).
* `/api/inventory/products/low_stock/` : (Custom GET Action) Chỉ lấy ra các Sản phẩm sắp cạn kho.
* `/api/inventory/products/summary/` : (Custom GET Action) Lấy thống kê tổng giá trị danh mục toàn kho.

> **💡 Lưu ý:** Để gửi yêu cầu Query tới các API trên ở công cụ như Postman hoặc giao diện Web, bạn cần tài khoản xác thực (có thể login bằng tài khoản `admin` thông qua Django Auth/Admin UI).

---

## Hướng dẫn cài đặt và chạy
1. Đảm bảo ở trong thư mục `day9`.
2. Khởi tạo môi trường ảo và cài đặt thư viện nhanh gọn với `uv`:
```bash
uv sync
```
3. Chạy Server:
```bash
uv run python manage.py runserver
```
*(Có thể mở link `http://127.0.0.1:8000/api/inventory/` trực tiếp trên trình duyệt để sử dụng Web Browsable API do DRF hỗ trợ render).*
