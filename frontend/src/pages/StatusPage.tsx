import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '../api/client';

export function StatusPage() {
  const health = useQuery({ queryKey: ['health'], queryFn: fetchHealth, refetchInterval: 30000, retry: 1 });
  return <main>
    <div className="eyebrow">KHỞI TẠO HỆ THỐNG / PHASE 01</div>
    <h1>Nền tảng cho những<br/>tuyến đường tốt hơn.</h1>
    <p className="intro">Road Damage Detection & GIS Dashboard — hệ thống quản lý dữ liệu hư hỏng mặt đường có thể truy vết.</p>
    <section className="panel" aria-labelledby="status-title">
      <div className="panel-head"><h2 id="status-title">Trạng thái kết nối</h2><button onClick={() => void health.refetch()} disabled={health.isFetching}>Kiểm tra lại</button></div>
      {health.isPending && <p role="status">Đang kiểm tra dịch vụ…</p>}
      {health.isError && <p role="alert">Không kết nối được API. Kiểm tra backend và cấu hình VITE_API_BASE_URL, sau đó thử lại.</p>}
      {health.data && <>
        <p role="status">{health.data.status === 'ok' ? 'Các dịch vụ đã sẵn sàng.' : 'Một số dịch vụ chưa sẵn sàng.'}</p>
        <div className="services">{([['database', 'PostgreSQL'], ['postgis', 'PostGIS'], ['schema', 'Migration'], ['redis', 'Redis']] as const).map(([key, label]) => <div className="service" key={key}><span>{label}</span><strong className={health.data[key]}>{health.data[key] === 'ok' ? 'Đã kết nối' : 'Chưa sẵn sàng'}</strong></div>)}</div>
      </>}
    </section>
    <section className="note"><h2>Phạm vi Phase 1</h2><p>Đã thiết lập nền tảng API, cơ sở dữ liệu không gian và hàng đợi worker. Upload, suy luận AI, bản đồ và thống kê được triển khai trong các giai đoạn tiếp theo.</p><p>Chưa có kết quả AI hoặc dữ liệu GPS. Dữ liệu thiếu tọa độ sẽ giữ trạng thái <code>unlocated</code>.</p></section>
  </main>;
}
