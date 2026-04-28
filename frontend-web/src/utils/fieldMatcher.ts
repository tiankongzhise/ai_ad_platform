/**
 * 智能字段匹配工具
 * 实现模糊匹配算法，将用户Excel列名匹配到标准字段
 */
import type { FieldMapping, FieldMappingResponse } from '@/types';

// 标准字段定义
export const STANDARD_FIELDS = [
  { key: 'name', label: '姓名', aliases: ['姓名', 'name', '名字', '学员姓名', '学生姓名', '客户姓名', '客户名称', 'username'] },
  { key: 'phone', label: '手机号', aliases: ['手机号', '手机', '电话', 'tel', 'phone', '联系方式', 'mobile', '移动电话', '联系电话'] },
  { key: 'source_channel', label: '来源渠道', aliases: ['渠道', '来源', 'source', 'channel', '广告渠道', '报名渠道', '获客渠道', '推广渠道'] },
  { key: 'course_name', label: '课程名称', aliases: ['课程', '课程名', 'course', '意向课程', '咨询课程', '产品名称', '课程产品'] },
  { key: 'deal_status', label: '成交状态', aliases: ['状态', '成交状态', '跟进状态', 'deal_status', 'deal', '意向度', '意向等级'] },
  { key: 'deal_amount', label: '成交金额', aliases: ['金额', '成交金额', 'deal_amount', '付款金额', '实收金额', '订单金额'] },
  { key: 'deal_date', label: '成交日期', aliases: ['日期', '成交日期', 'deal_date', '报名日期', '付款日期', '跟进日期'] },
  { key: 'wechat', label: '微信号', aliases: ['微信', 'wechat', 'wx', 'wxid', '微信公众号'] },
  { key: 'qq', label: 'QQ号', aliases: ['qq', 'QQ', 'qq号'] },
  { key: 'email', label: '邮箱', aliases: ['邮箱', 'email', '邮件', 'E-mail'] },
  { key: 'gender', label: '性别', aliases: ['性别', 'gender', 'sex', '男', '女'] },
  { key: 'age', label: '年龄', aliases: ['年龄', 'age'] },
  { key: 'city', label: '城市', aliases: ['城市', 'city', '所在城市', '地区', '地址'] },
  { key: 'remark', label: '备注', aliases: ['备注', 'remark', '备注信息', '说明', '其他备注'] },
] as const;

type StandardFieldKey = typeof STANDARD_FIELDS[number]['key'];

/**
 * 计算两个字符串的相似度（简单实现）
 * 返回 0-1 的相似度分数
 */
function calculateSimilarity(str1: string, str2: string): number {
  const s1 = str1.toLowerCase().trim();
  const s2 = str2.toLowerCase().trim();

  if (s1 === s2) return 1;
  if (s1.includes(s2) || s2.includes(s1)) return 0.8;

  // 计算编辑距离
  const len1 = s1.length;
  const len2 = s2.length;
  const maxLen = Math.max(len1, len2);

  if (maxLen === 0) return 1;

  const dp: number[][] = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));

  for (let i = 0; i <= len1; i++) dp[i][0] = i;
  for (let j = 0; j <= len2; j++) dp[0][j] = j;

  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      const cost = s1[i - 1] === s2[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + cost
      );
    }
  }

  return 1 - dp[len1][len2] / maxLen;
}

/**
 * 匹配单个列名到标准字段
 */
function matchColumn(columnName: string): { field: string; label: string; confidence: 'auto' | 'suggested' | 'none' } | null {
  const trimmed = columnName.trim();

  for (const field of STANDARD_FIELDS) {
    // 检查别名匹配
    for (const alias of field.aliases) {
      const similarity = calculateSimilarity(trimmed, alias);
      if (similarity >= 0.9) {
        return { field: field.key, label: field.label, confidence: 'auto' };
      }
    }

    // 检查模糊匹配
    for (const alias of field.aliases) {
      const similarity = calculateSimilarity(trimmed, alias);
      if (similarity >= 0.6) {
        return { field: field.key, label: field.label, confidence: 'suggested' };
      }
    }
  }

  return null;
}

/**
 * 匹配所有列名
 */
export function matchFields(userColumns: string[]): FieldMappingResponse {
  const fieldMappings: FieldMapping[] = [];
  const matchedFields = new Set<string>();

  for (const column of userColumns) {
    const match = matchColumn(column);

    if (match && !matchedFields.has(match.field)) {
      fieldMappings.push({
        field: match.field,
        matchedColumn: column,
        confidence: match.confidence,
      });
      matchedFields.add(match.field);
    } else {
      fieldMappings.push({
        field: '',
        matchedColumn: column,
        confidence: 'none',
      });
    }
  }

  // 找出未匹配的必填字段
  const requiredFields = ['name', 'phone'];
  const unmatchedRequired = requiredFields.filter(f => !matchedFields.has(f));

  return {
    batch_id: '',
    columns: userColumns,
    field_mappings: fieldMappings,
    unmatched_fields: unmatchedRequired,
  };
}

/**
 * 获取字段的中文标签
 */
export function getFieldLabel(key: string): string {
  const field = STANDARD_FIELDS.find(f => f.key === key);
  return field?.label || key;
}

/**
 * 获取字段的图标
 */
export function getFieldIcon(key: string): string {
  const icons: Record<string, string> = {
    name: 'UserOutlined',
    phone: 'PhoneOutlined',
    source_channel: 'ShopOutlined',
    course_name: 'BookOutlined',
    deal_status: 'CheckCircleOutlined',
    deal_amount: 'YenOutlined',
    deal_date: 'CalendarOutlined',
    wechat: 'MessageOutlined',
    qq: 'QqOutlined',
    email: 'MailOutlined',
    gender: 'ManOutlined',
    age: 'HourglassOutlined',
    city: 'EnvironmentOutlined',
    remark: 'FileTextOutlined',
  };
  return icons[key] || 'FileOutlined';
}
