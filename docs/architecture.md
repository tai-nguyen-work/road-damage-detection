# Kiến trúc Phase 1

Browser → Nginx (frontend React) → `/api/v1` → FastAPI → PostgreSQL 16/PostGIS.
Redis + RQ worker nghe queue `processing`; chưa có producer hoặc detector trong Phase 1.
Service `migrate` tạo extension PostGIS và schema trước khi API/worker khởi động.

Bốn bảng: media, processing_jobs, detections, gps_track_points. Tọa độ dùng
geography(Point,4326), nullable khi chưa định vị. Không có seed/demo data.
Timestamp là TIMESTAMPTZ; kết nối DB dùng UTC. API GeoJSON Phase 3 sẽ dùng lon, lat.
GPS camera chỉ mô tả vị trí thiết bị, không bảo đảm vị trí chính xác của hư hỏng.

Alembic revision đầu chứa bản schema đóng băng riêng; không import models ứng dụng.
Job đang queued/running có unique partial index theo media; detection có foreign key
kép bảo đảm job và media khớp nhau. Nhãn gốc được lưu riêng, không áp mapping RDD mặc định.
Các phase sau bổ sung validation tại API cho kích thước bbox và provenance đầy đủ.

Health là readiness: kiểm tra DB, PostGIS, Alembic revision và Redis. HTTP 503 khi
bất kỳ phụ thuộc nào lỗi, không trả exception chứa thông tin kết nối ra client.
Compose dùng restart policy; RQ hỗ trợ graceful shutdown qua SIGTERM. Worker Phase 1
chỉ đợi job, không giả lập kết quả AI.

Alembic giới hạn search_path=public và bỏ qua spatial_ref_sys thuộc PostGIS, tránh
tự sinh lệnh xóa bảng extension/tiger/topology. Tài liệu tham chiếu:
[SQLAlchemy declarative](https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html),
[Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/).
