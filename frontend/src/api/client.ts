import type { Health } from '../types/health';
const baseUrl = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
export async function fetchHealth(): Promise<Health> {
  const response = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(12000) });
  if (!response.ok && response.status !== 503) throw new Error(`API trả HTTP ${response.status}`);
  const data: unknown = await response.json();
  if (!data || typeof data !== 'object' || !('status' in data) ||
      !['ok', 'degraded'].includes(String(data.status)) ||
      !['database', 'postgis', 'schema', 'redis'].every(key =>
        key in data && ['ok', 'error'].includes(String((data as Record<string, unknown>)[key])))) {
    throw new Error('Phản hồi health không hợp lệ');
  }
  return data as Health;
}
