import type { DashboardData } from '../types/dashboard';
import { DEMO_DATA } from './demoData';

export async function loadDashboardData(): Promise<DashboardData> {
  try {
    const res = await fetch('/dashboard_data.json');
    if (!res.ok) throw new Error('Not found');
    return (await res.json()) as DashboardData;
  } catch {
    console.warn('[Dashboard] dashboard_data.json not found — using demo data.');
    return DEMO_DATA;
  }
}

export function fmtPct(val: number, decimals = 2): string {
  return `${(val * 100).toFixed(decimals)}%`;
}

export function fmtNum(val: number, decimals = 2): string {
  return val.toFixed(decimals);
}

export const MONTH_LABELS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
