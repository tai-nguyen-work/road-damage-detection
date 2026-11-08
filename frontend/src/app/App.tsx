import { Link, Route, Routes } from 'react-router-dom';
import { StatusPage } from '../pages/StatusPage';
export function App() {
  return <><header><Link className="brand" to="/">◈ <span>ROAD DAMAGE<small>GIS & VISION PLATFORM</small></span></Link><span className="badge">PHASE 1</span></header><Routes><Route path="/" element={<StatusPage/>}/><Route path="*" element={<main><h1>Không tìm thấy trang</h1><Link to="/">Về trang trạng thái</Link></main>}/></Routes><footer>Road Damage Detection · Dữ liệu có nguồn gốc, vị trí có kiểm chứng.</footer></>;
}
