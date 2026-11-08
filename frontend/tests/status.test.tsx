import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, cleanup } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { StatusPage } from '../src/pages/StatusPage';

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function renderPage() {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><StatusPage/></QueryClientProvider>);
}
it('hiển thị trạng thái từ API', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({status:'ok',database:'ok',postgis:'ok',schema:'ok',redis:'ok'}))));
  renderPage();
  expect(await screen.findByText('Các dịch vụ đã sẵn sàng.')).toBeInTheDocument();
  expect(screen.getAllByText('Đã kết nối')).toHaveLength(4);
});
it('hiển thị phụ thuộc lỗi khi API trả 503', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({status:'degraded',database:'error',postgis:'error',schema:'error',redis:'ok'}), {status:503})));
  renderPage();
  expect(await screen.findByText('Một số dịch vụ chưa sẵn sàng.')).toBeInTheDocument();
});
it('hiển thị lỗi kết nối', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
  renderPage();
  expect(await screen.findByRole('alert', {}, { timeout: 4000 })).toHaveTextContent('Không kết nối được API');
});
