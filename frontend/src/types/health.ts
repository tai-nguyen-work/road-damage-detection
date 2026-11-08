export type DependencyStatus = 'ok' | 'error';
export interface Health {
  status: 'ok' | 'degraded';
  database: DependencyStatus;
  postgis: DependencyStatus;
  schema: DependencyStatus;
  redis: DependencyStatus;
}
