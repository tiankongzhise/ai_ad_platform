/**
 * 格式化工具函数
 */

/**
 * 格式化货币
 */
export function formatCurrency(value: number, unit: '¥' | '$' | 'HK$' = '¥'): string {
  if (value >= 10000) {
    return `${unit}${(value / 10000).toFixed(2)}万`;
  }
  return `${unit}${value.toFixed(2)}`;
}

/**
 * 格式化数字
 */
export function formatNumber(value: number): string {
  if (value >= 10000) {
    return `${(value / 10000).toFixed(2)}万`;
  }
  return value.toLocaleString();
}

/**
 * 格式化百分比
 */
export function formatPercent(value: number, decimals: number = 2): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * 格式化趋势值
 */
export function formatTrend(value: number, decimals: number = 1): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

/**
 * 格式化日期
 */
export function formatDate(date: string | Date, format: 'full' | 'date' | 'time' = 'date'): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  switch (format) {
    case 'full':
      return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    case 'time':
      return `${hours}:${minutes}:${seconds}`;
    default:
      return `${year}-${month}-${day}`;
  }
}

/**
 * 相对时间格式化
 */
export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diff = now.getTime() - d.getTime();

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return '刚刚';
  if (minutes < 60) return `${minutes}分钟前`;
  if (hours < 24) return `${hours}小时前`;
  if (days < 7) return `${days}天前`;
  
  return formatDate(d, 'date');
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * 截断字符串
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength)}...`;
}
