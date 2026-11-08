# AGENTS.md — Hướng dẫn Codex xây dựng hệ thống phát hiện hư hỏng mặt đường

## 1. Vai trò và mục tiêu
Bạn là kỹ sư phần mềm full-stack kiêm kỹ sư thị giác máy tính. Hãy xây dựng ứng dụng **Road Damage Detection & GIS Dashboard** có thể chạy thực tế, sử dụng **YOLO26 (Ultralytics, nếu phiên bản cài đặt hỗ trợ)**, **Python/FastAPI**, **ReactJS/TypeScript**, **PostgreSQL/PostGIS**.

Mục tiêu: tải ảnh/video mặt đường; nhận diện các loại hư hỏng; lưu bounding box, nhãn, độ tin cậy và vị trí GPS có nguồn gốc rõ ràng; hiển thị bản đồ, danh sách và thống kê trên dashboard; cho phép xem chi tiết và lọc kết quả.

**Nguyên tắc quan trọng:** Không được tự bịa tọa độ, độ chính xác GPS, kết quả suy luận AI hay metric. Ảnh không chứa thông tin GPS phải được gắn trạng thái `unlocated` cho đến khi người dùng nhập tọa độ hợp lệ hoặc cung cấp track GPS được đồng bộ thời gian.

## 2. Quy tắc thực thi cho Codex
1. Đọc toàn bộ tài liệu trước khi viết mã; khảo sát repo và giữ lại phần đang hoạt động.
2. Triển khai theo từng giai đoạn, mỗi giai đoạn chạy lint/test và báo cáo file đã thay đổi.
3. Ưu tiên mã chạy được end-to-end, không để TODO cho luồng cốt lõi. Không hardcode dữ liệu demo vào luồng production.
4. Mọi khóa bí mật qua `.env`; chỉ commit `.env.example`. Không ghi thông tin nhạy cảm vào log.
5. Dùng type hints Python, Pydantic schemas, TypeScript strict, validation đầu vào, error handling và logging có cấu trúc.
6. Viết README hướng dẫn chạy local, Docker Compose, migration, training và inference.
7. Nếu môi trường không có GPU hoặc checkpoint phù hợp, cung cấp chế độ CPU và mock detector **chỉ cho test**, được đánh dấu rõ ràng; không báo mock là kết quả AI thật.
8. Không tự nhận YOLO26 hỗ trợ API/model name nào khi chưa xác minh từ phiên bản Ultralytics đã khóa. Kiểm tra tài liệu và khả năng load checkpoint thực tế; nếu không tương thích, báo lỗi có hướng dẫn thay vì âm thầm thay mô hình.
9. Dùng UTC trong DB/API cho timestamp; frontend hiển thị múi giờ người dùng. Tọa độ dùng WGS84, `EPSG:4326`, thứ tự API là `longitude, latitude` khi dùng GeoJSON.

## 3. Công nghệ
- Frontend: ReactJS + TypeScript + Vite, React Router, TanStack Query, Tailwind CSS, Leaflet + React Leaflet, Recharts.
- Backend: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2, Alembic, Pydantic v2.
- AI: Ultralytics YOLO26 qua checkpoint có thể cấu hình, OpenCV, Pillow, NumPy.
- Database: PostgreSQL 16 + PostGIS; GeoAlchemy2 cho dữ liệu địa lý.
- Storage: local filesystem cho MVP, thiết kế abstraction để chuyển sang S3/MinIO.
- Background jobs: dùng worker hàng đợi (ví dụ Redis + RQ/Celery) cho video và tác vụ nặng; API trả job ID, không giữ HTTP request cho toàn bộ video.
- Deployment: Docker Compose cho frontend, API, worker, PostgreSQL/PostGIS, Redis.
- Testing: pytest, httpx, Vitest, React Testing Library; Playwright cho smoke E2E nếu môi trường hỗ trợ.

## 4. Kiến trúc xử lý
1. Người dùng upload ảnh/video, có thể nhập GPS hoặc upload GPS track CSV/GPX với timestamp.
2. Backend kiểm tra định dạng, kích thước, quyền truy cập, metadata và tạo `media` + `processing_job`.
3. Worker xử lý ảnh hoặc lấy frame video theo cấu hình, chạy model YOLO26, trả bbox, class, confidence.
4. Bộ định vị lấy GPS từ EXIF hợp lệ, GPS người dùng nhập, hoặc nội suy từ GPS track theo timestamp đã đồng bộ. Ghi `location_source`, `location_accuracy_m` nếu có, và trạng thái định vị.
5. Lưu detection liên kết media/frame, tọa độ điểm (nếu có), thời gian, model version; lưu ảnh annotation/thumbnail.
6. Dashboard lấy GeoJSON để vẽ marker/cluster và hiển thị danh sách, bộ lọc, thống kê.

**Lưu ý:** GPS của camera biểu thị vị trí thiết bị, không nhất thiết là vị trí chính xác của ổ gà trong ảnh. Đặt trường `location_method` (`camera_gps`, `manual`, `track_interpolated`, `surveyed`) và mô tả sai số; không tuyên bố geolocation của từng vật thể chính xác nếu chưa có hiệu chuẩn camera/định vị hình học.

## 5. Cấu trúc thư mục mục tiêu
```text
road-damage-system/
├── AGENTS.md
├── README.md
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/          # config, security, logging
│   │   ├── api/v1/        # routers
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic DTOs
│   │   ├── services/      # media, detection, geolocation, statistics
│   │   ├── ai/            # YOLO adapter, preprocessing, postprocessing
│   │   ├── workers/       # async processing jobs
│   │   └── db/
│   ├── tests/
│   └── scripts/          # training/evaluation/import GPS
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   ├── pages/         # Dashboard, Map, Upload, Detections, Detail
│   │   ├── components/    # MapView, Filters, Charts, UploadForm
│   │   ├── features/
│   │   ├── api/
│   │   ├── hooks/
│   │   ├── types/
│   │   └── utils/
│   └── tests/
├── datasets/             # gitignored; chỉ chứa ví dụ cấu trúc
└── docs/                 # architecture, API, dataset, deployment
```

## 6. Mô hình dữ liệu
Tạo migration cho các bảng tối thiểu:

### `media`
- `id` UUID PK; `kind` enum `image|video`; `original_filename`, `mime_type`, `storage_path`, `sha256`, `width`, `height`, `duration_ms` nullable, `captured_at` nullable, `uploaded_at`, `status`.
- `gps_point` geography(Point,4326) nullable; `location_source`, `location_accuracy_m` nullable; `gps_timestamp` nullable.

### `processing_jobs`
- `id` UUID PK; `media_id` FK; `status` enum `queued|running|completed|failed`; `progress` 0–100; `error_message` nullable; `created_at`, `started_at`, `finished_at`; `model_version`; `config_json`.

### `detections`
- `id` UUID PK; `media_id` FK; `job_id` FK; `frame_index` nullable; `frame_timestamp_ms` nullable; `damage_type`; `confidence` float 0..1; `bbox_x1`, `bbox_y1`, `bbox_x2`, `bbox_y2` (pixel, gốc trên-trái); `point` geography(Point,4326) nullable; `location_method`, `location_accuracy_m` nullable; `detected_at`; `model_version`; `annotated_image_path` nullable.
- Index cho `damage_type`, `detected_at`, `media_id`; GiST index cho `point`.

### `gps_track_points`
- `id`, `media_id` FK, `recorded_at` UTC, `point` geography(Point,4326), `accuracy_m` nullable; index `(media_id, recorded_at)`.

Dùng enum/mapping nhãn cấu hình, không khóa cứng số lớp nếu dataset khác. Ví dụ RDD2022: `D00` nứt dọc, `D10` nứt ngang, `D20` nứt dạng lưới, `D40` ổ gà; chỉ áp dụng mapping này khi dataset thực sự sử dụng quy ước đó. Cho phép lớp `other` và lưu nhãn gốc.

## 7. REST API v1
Prefix `/api/v1`; OpenAPI tự sinh và có ví dụ request/response.

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/media/upload` | Upload ảnh/video multipart + GPS tùy chọn |
| GET | `/media` | Danh sách media có phân trang |
| GET | `/media/{id}` | Chi tiết media |
| POST | `/media/{id}/process` | Tạo job suy luận, chống tạo trùng ngoài ý muốn |
| GET | `/jobs/{id}` | Trạng thái và tiến độ |
| GET | `/detections` | Danh sách, phân trang, lọc loại/confidence/thời gian |
| GET | `/detections/{id}` | Chi tiết detection |
| GET | `/detections/geojson` | FeatureCollection, lọc bbox bản đồ và loại lỗi |
| GET | `/stats/summary` | Tổng quan theo loại, thời gian, số media |
| POST | `/media/{id}/gps-track` | Upload GPS track CSV/GPX |
| PATCH | `/media/{id}/location` | Cập nhật vị trí thủ công, ghi nguồn gốc |

API GeoJSON: mỗi Feature có `geometry: Point` tọa độ `[longitude, latitude]`, `properties` gồm `id`, `damage_type`, `confidence`, `detected_at`, `thumbnail_url`, `media_id`, `location_method`. **Không đưa detection thiếu tọa độ vào GeoJSON**; chúng vẫn xuất hiện trong danh sách với trạng thái `unlocated`.

Yêu cầu chung: validate lat trong [-90,90], lon trong [-180,180], confidence trong [0,1], bbox hợp lệ; limit upload và pagination; CORS cấu hình; trả HTTP status đúng; tránh path traversal và file độc hại. Endpoint GeoJSON phải có giới hạn số kết quả và lọc theo viewport để tránh quá tải.

## 8. Pipeline YOLO26
- Cấu hình `YOLO_MODEL_PATH`, `YOLO_CONFIDENCE_THRESHOLD`, `YOLO_IOU_THRESHOLD`, `YOLO_DEVICE`, `YOLO_IMAGE_SIZE` qua env.
- Khởi tạo model một lần mỗi worker; không load lại cho từng ảnh.
- Tách `Detector` interface và `UltralyticsDetector`; `MockDetector` chỉ dành cho automated tests.
- Chuẩn hóa EXIF orientation, đọc kích thước gốc, kiểm tra bbox; xuất bounding boxes ở hệ tọa độ pixel của ảnh hiển thị.
- Với video: sample frame theo FPS hoặc khoảng thời gian cấu hình; lưu `frame_timestamp_ms`; xử lý lỗi frame và giải phóng tài nguyên.
- Tránh đếm trùng như thể mỗi frame là một vị trí hư hỏng độc lập. Trong MVP hiển thị detection theo frame và giải thích giới hạn; nếu bổ sung tracking/dedup thì triển khai thuật toán rõ ràng và có test.
- Lưu `model_version`, confidence, class mapping và cấu hình inference để truy vết.
- Training tùy chọn: scripts chuẩn bị dataset YOLO, chia train/val/test theo tuyến đường hoặc video để giảm data leakage; training, validation, export metrics (precision, recall, mAP50, mAP50-95), confusion matrix. Không tự tạo metric.
- Trước khi code, kiểm tra package Ultralytics được cài có hỗ trợ checkpoint YOLO26 mong muốn. Checkpoint pretrained chung có thể không nhận diện lớp hư hỏng; cần fine-tune bằng dataset mặt đường và cấu hình `data.yaml`.

## 9. Định vị GPS
- Ảnh: đọc EXIF GPS khi tồn tại và hợp lệ; hỗ trợ nhập lat/lon thủ công.
- Video: không mặc định video chứa GPS; hỗ trợ track CSV (`timestamp,latitude,longitude,accuracy_m`) hoặc GPX.
- Đồng bộ timestamp frame với timestamp GPS track qua thời điểm bắt đầu ghi hình được khai báo; nội suy tuyến tính chỉ giữa hai điểm hợp lệ và khi khoảng cách thời gian dưới ngưỡng cấu hình; không ngoại suy ngoài track.
- Bản ghi không định vị được phải giữ `point=NULL` và `location_status=unlocated` ở tầng API/DTO (có thể suy ra từ `point`).
- Hiển thị nguồn tọa độ và cảnh báo rằng camera GPS là vị trí gần đúng của hư hỏng.

## 10. Giao diện React Dashboard
Thiết kế responsive, tiếng Việt, dễ sử dụng:
1. **Dashboard:** KPI tổng số detection, media, điểm đã định vị, điểm chưa định vị; biểu đồ theo loại lỗi và theo thời gian.
2. **Bản đồ:** OpenStreetMap + Leaflet, marker clustering, màu/icon phân loại, popup gồm nhãn, confidence, thời gian, ảnh thumbnail, nguồn GPS và nút xem chi tiết. Có filter loại hư hỏng, confidence, thời gian; đồng bộ viewport với API bbox.
3. **Upload:** kéo thả ảnh/video, xem trước, nhập GPS tùy chọn hoặc GPS track, thanh tiến độ upload và trạng thái job.
4. **Danh sách:** bảng có tìm kiếm, filter, pagination, liên kết sang chi tiết và định vị trên bản đồ.
5. **Chi tiết:** ảnh gốc và ảnh có bbox, nhãn, confidence, tọa độ (nếu có), nguồn GPS, model version, thời gian.
6. **Trạng thái:** loading, empty, error, retry; thông báo rõ khi chưa có GPS, không đặt marker giả.

Sử dụng TanStack Query cho fetch/cache, typed API client, env `VITE_API_BASE_URL`, xử lý lỗi HTTP. Chú ý tile attribution theo điều khoản của nhà cung cấp bản đồ; không phụ thuộc vào tile OSM công cộng cho tải production lớn.

## 11. Bảo mật và vận hành
- Giới hạn kích thước upload, allowlist MIME/extension, kiểm tra nội dung thực tế, tạo filename UUID và lưu ngoài thư mục public tùy tiện.
- Không cho phép client gửi đường dẫn filesystem tùy ý; media endpoint phục vụ file đã được kiểm soát.
- Với MVP local có thể chưa có đăng nhập, nhưng ghi rõ đây là giới hạn; trước production cần auth, phân quyền, rate limiting, retention và chính sách bảo vệ dữ liệu vị trí.
- Health checks, DB migration, structured logs, retry job có giới hạn, cleanup file tạm, graceful shutdown.
- Cung cấp `.env.example`, Dockerfile, `docker-compose.yml`, volume DB/storage và hướng dẫn CPU/GPU.

## 12. Các giai đoạn Codex phải thực hiện
### Phase 1 — Khởi tạo
Tạo monorepo, backend/frontend skeleton, Docker Compose, `.env.example`, README, health API, kết nối PostGIS và migration. Xác minh khởi động được.

### Phase 2 — AI & upload
Upload ảnh, storage, adapter YOLO26, worker/job, lưu detection, trả ảnh annotated; test bằng ảnh mẫu hợp lệ. Không cần dataset training để hoàn thiện API, nhưng phải báo rõ khi chưa có model fine-tuned.

### Phase 3 — GPS & bản đồ
EXIF/manual GPS, GPS track video, GeoJSON API, PostGIS indexes, React Leaflet map và marker popup; đảm bảo unlocated không hiện trên bản đồ.

### Phase 4 — Dashboard
KPI, biểu đồ, bộ lọc, danh sách, trang chi tiết, UX loading/error/empty, responsive.

### Phase 5 — Kiểm thử và hoàn thiện
Unit/integration/E2E smoke, tài liệu API, lệnh setup/training/inference, kiểm tra lỗi và tối ưu.

## 13. Tiêu chí nghiệm thu (Definition of Done)
- `docker compose up --build` chạy được các service cần thiết sau khi cấu hình env và checkpoint phù hợp.
- Upload một ảnh có GPS → job hoàn tất → detection thật được lưu → marker đúng tọa độ → popup xem chi tiết.
- Upload ảnh không có GPS → vẫn xem detection trong danh sách nhưng **không có marker**.
- Upload video + track GPS có timestamp → frame được gán tọa độ hợp lệ; track thiếu hoặc không đồng bộ → không bịa tọa độ.
- Bộ lọc bản đồ và danh sách hoạt động; thống kê phản ánh DB, không hardcode.
- Migration chạy sạch trên database mới; API có OpenAPI; tests backend/frontend pass.
- README có hướng dẫn thiết lập, dữ liệu mẫu, nguồn checkpoint, hạn chế độ chính xác và troubleshooting.

## 14. Lệnh gợi ý (điều chỉnh theo mã thực tế)
```bash
cp .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend pytest
cd frontend && npm install && npm run lint && npm run test && npm run build
```

## 15. Yêu cầu khi trả lời sau mỗi phase
Báo cáo ngắn: (1) chức năng đã làm; (2) file quan trọng đã tạo/sửa; (3) lệnh đã chạy và kết quả thực tế; (4) hạn chế hoặc blocker; (5) bước tiếp theo. Không tuyên bố test pass nếu chưa chạy.

## 16. Prompt khởi động cho Codex
> Đọc AGENTS.md và triển khai Phase 1 của hệ thống Road Damage Detection. Kiểm tra repository hiện tại, đề xuất kế hoạch ngắn, sau đó viết code thực tế, chạy các lệnh kiểm tra khả dụng và báo cáo kết quả. Không chuyển sang phase kế tiếp trước khi Phase 1 chạy ổn định. Tuân thủ quy tắc không bịa GPS, kết quả AI hoặc metric.
