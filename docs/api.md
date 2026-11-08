# API Phase 1

- Swagger UI: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json
- `GET /api/v1/health`: 200 khi DB, PostGIS, schema và Redis sẵn sàng; 503 khi lỗi.

```json
{"status":"ok","database":"ok","postgis":"ok","schema":"ok","redis":"ok"}
```

Đây là ví dụ contract, không phải báo cáo trạng thái thực tế.
Các API upload, jobs, detections, GPS và statistics chưa triển khai trong Phase 1.
