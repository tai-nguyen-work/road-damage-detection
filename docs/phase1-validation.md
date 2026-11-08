# Kết quả kiểm tra Phase 1 — 08/11/2026

Đã chạy thực tế:

- `ruff check backend`: pass.
- Backend pytest trên máy local: **5 passed** khi có TEST_DATABASE_URL trỏ đến
  database PostGIS test riêng (4 unit + 1 integration). Có một cảnh báo deprecation
  từ Starlette TestClient/httpx; không ảnh hưởng kết quả hiện tại.
- Database test mới: `alembic upgrade head`, `downgrade base`, `upgrade head`:
  pass; `alembic check`: không phát hiện schema drift.
- Backend trong Docker Python 3.11: **4 passed, 1 skipped** vì chưa truyền
  TEST_DATABASE_URL; ruff và `alembic check` pass khi dùng cache trong /tmp.
- Frontend: `npm run lint`, `npm run test` (**3 passed**), `npm run build`: pass.
- `docker compose config --quiet`: pass.
- Một bản stack đã build/khởi động thành công: DB, Redis, API, frontend healthy;
  migrate exit 0; RQ worker nghe queue processing.
- HTTP thực: API health 200, frontend 200, Nginx `/api/v1/health` proxy 200;
  database/postgis/schema/redis đều `ok`.

Giới hạn xác minh bản cuối:

- Khi đồng bộ lockfile, lần rebuild Linux phát hiện optional bundled dependencies
  của Tailwind bị thiếu. Đã tái tạo và chuẩn hóa lockfile giữ đủ dependency;
  `npm ci --dry-run --ignore-scripts --offline --no-audit --no-fund` pass,
  rồi chạy lại frontend lint/test/build đều pass.
- Yêu cầu cấp quyền chạy lại `docker compose up --build -d` sau sửa lockfile bị
  từ chối. Vì vậy **chưa xác nhận build Docker cuối cùng**; stack đã chạy là bản
  trước các chỉnh sửa lockfile/cache cuối. Không coi dry-run là Linux build thành công.
- `npm audit` còn 7 mục moderate trong chuỗi dependency lint
  (typescript-eslint/minimatch), không còn high/critical tại thời điểm kiểm tra.
- Chưa chạy browser E2E, YOLO hoặc suy luận; các phần đó ngoài Phase 1.

Bước tiếp theo: chạy lại `docker compose up --build -d`, kiểm tra health và
`docker compose exec backend ruff check .` trước khi chuyển sang Phase 2.
