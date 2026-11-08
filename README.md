# Road Damage Detection & GIS Dashboard

Phase 1: nền tảng FastAPI, React/TypeScript, PostgreSQL 16/PostGIS, Alembic,
Redis/RQ và Docker Compose. Giao diện tiếng Việt đọc trạng thái thật từ health API.
Chưa triển khai upload, inference, bản đồ hoặc thống kê; không kèm dữ liệu GPS/AI giả.

## Chạy bằng Docker Compose

Cần Docker Engine/Desktop đang chạy và Docker Compose v2.

```bash
cp .env.example .env
# Sửa POSTGRES_PASSWORD và DATABASE_URL tương ứng trong .env
# Mật khẩu trong URL phải percent-encode ký tự đặc biệt.
docker compose up --build -d
docker compose ps -a
curl --fail http://localhost:8000/api/v1/health
```

- Frontend: http://localhost:8080
- API/Swagger: http://localhost:8000/docs
- DB: localhost:5432; Redis: localhost:6379 (chỉ bind loopback).

Compose đợi DB/Redis healthy, tự chạy `alembic upgrade head` qua service `migrate`,
rồi khởi động API, worker và frontend. `migrate` kết thúc mã 0 là bình thường.
Tag PostGIS đang dùng chỉ có amd64; Compose khai báo `platform: linux/amd64`.
Máy ARM cần bật x86_64 emulation trong Docker Desktop hoặc dùng image PostGIS 16
tương thích kiến trúc sau khi kiểm tra. Không dùng SQLite thay PostGIS.

```bash
docker compose logs --tail=100 migrate backend worker
docker compose exec backend alembic current
docker compose exec backend pytest
docker compose exec backend ruff check .
docker compose stop
```

DB, Redis và storage dùng named volume. `docker compose down` giữ dữ liệu;
không chạy `down -v` trừ khi chủ động muốn xóa toàn bộ dữ liệu.

## Chạy development local

Dùng Python 3.11 (giống Docker), Node.js 22.12+ và npm.

```bash
cp .env.example .env
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e './backend[dev]'
docker compose up -d db redis
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal thứ hai:

```bash
cd frontend
npm ci
npm run dev
```

Mở http://localhost:5173. Vite proxy `/api` tới localhost:8000; Nginx trong Docker
proxy tới backend:8000. `VITE_API_BASE_URL` mặc định `/api/v1`; nếu cần đổi khi dev,
đặt trong `frontend/.env.local`. Với Docker, biến này được dùng lúc build frontend.
CORS cấu hình bằng JSON array `CORS_ORIGINS`; không dùng wildcard credentials.

## Migration và kiểm thử

```bash
cd backend
ruff check .
pytest
alembic upgrade head
alembic check
# Chỉ dùng database test riêng đã migrate, không dùng DB production:
TEST_DATABASE_URL=postgresql+psycopg://road:PASSWORD@localhost:5432/road_damage_test pytest
# Migration mới sau khi sửa models:
alembic revision --autogenerate -m "describe change"
```

Integration test tự skip nếu thiếu `TEST_DATABASE_URL`; unit test health thay thế
phụ thuộc chỉ trong test, không tạo kết quả AI. Integration test kiểm tra PostGIS,
schema và tọa độ NULL, rollback bản ghi test. Trên DB test có thể kiểm tra vòng migration
bằng `alembic downgrade base` rồi `alembic upgrade head` (downgrade sẽ xóa bảng).

```bash
cd frontend
npm run lint
npm run test
npm run build
```

## AI, CPU/GPU và dữ liệu

Phase 1 chưa cài Ultralytics, chưa load checkpoint và chưa xác minh YOLO26.
Các biến `YOLO_*` trong `.env.example` dành cho Phase 2; hiện không chạy inference
hoặc training. Không có lệnh training/inference được giả định hoạt động ở phase này.
Phase 2 phải khóa phiên bản Ultralytics, kiểm tra load checkpoint thực tế và lớp nhãn
fine-tuned trên dữ liệu mặt đường trước khi triển khai adapter. Pretrained chung
không được xem là model phát hiện hư hỏng. CPU là cấu hình dự kiến mặc định;
GPU cần PyTorch/CUDA, NVIDIA Container Toolkit và Compose override tương thích.
Dữ liệu thực và checkpoint không commit; xem [datasets](datasets/README.md).

## Giới hạn vận hành và xử lý lỗi

MVP local chưa có auth, phân quyền, rate limiting hay retention; chưa phù hợp để
mở ra Internet. Bí mật đặt trong `.env` (gitignored), chỉ `.env.example` được commit.
DB timestamps dùng UTC; tọa độ WGS84, GeoJSON sẽ theo thứ tự longitude, latitude.
Thiếu GPS phải giữ NULL/unlocated; GPS camera không phải phép đo tọa độ từng vật thể.

- Docker không kết nối được: khởi động Docker Engine/Desktop rồi chạy lại.
- Health 503: xem JSON phụ thuộc lỗi, logs backend, trạng thái migrate, DB và Redis.
- Migration lỗi credentials: đồng bộ `.env`; thay mật khẩu env không tự đổi mật khẩu
  của PostgreSQL đã có volume. Cập nhật role bằng quản trị DB, tránh xóa volume để chữa lỗi.
- Port đã dùng: đổi host port trong Compose và URL tương ứng.
- API không phản hồi ở frontend: kiểm tra proxy và `VITE_API_BASE_URL`, build lại khi đổi env.
- Cập nhật dependency: kiểm tra advisory, cập nhật pin/lock và chạy lại lint/test/build.

Xem [kiến trúc](docs/architecture.md), [API](docs/api.md), và [AGENTS.md](AGENTS.md).
Phase tiếp theo chỉ bắt đầu sau khi xác minh được Phase 1 khởi động với PostGIS thực.

Kết quả kiểm tra thực tế và phần còn cần xác minh: [báo cáo Phase 1](docs/phase1-validation.md).
