# BUG-06: AdAccount.balance 字段类型不一致

## Bug 描述

**严重级别**: 🟠 P1
**来源**: 代码审核 P1-2
**文件**: `backend/app/models/ad_account.py`

ORM 模型中 Python 类型 `Mapped[Optional[float]]` 与 SQLAlchemy 列类型 `BigInteger` 冲突。BigInteger 存储整数，但 Python 类型声明为 float，导致存储小数余额时被截断。广告账户余额单位应为"元"，应使用 `Numeric(18, 2)` 精确存储。

同时 `ad_daily_stat.py` 中存在相同问题：
- `spend: Mapped[float]` + `BigInteger` → 应改为 `Mapped[int]` + `Integer`（单位：分）
- `cost_per_click/cost_per_form: Mapped[Optional[float]]` + `BigInteger` → 应改为 `Numeric(18, 2)`

## 修复方案

### AdAccount.balance
```python
# 修复前
balance: Mapped[Optional[float]] = mapped_column(BigInteger, nullable=True, default=0)

# 修复后 — 单位为"元"，使用 Numeric 精确存储
balance: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True, default=0)
```

### AdDailyStat 核心指标
```python
# 修复前
spend: Mapped[float] = mapped_column(BigInteger, default=0, nullable=False)

# 修复后 — 单位为"分"，使用 Integer
spend: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
```

### AdDailyStat 计算指标
```python
# 修复前
cost_per_click: Mapped[Optional[float]] = mapped_column(BigInteger, nullable=True)

# 修复后 — 使用 Numeric 精确存储
cost_per_click: Mapped[Optional[float]] = mapped_column(Numeric(18, 2), nullable=True)
```

## 修复文件清单

| 文件 | 修改内容 |
|------|---------|
| `backend/app/models/ad_account.py` | balance 字段从 BigInteger 改为 Numeric(18, 2) |
| `backend/app/models/ad_daily_stat.py` | spend 改为 Integer，cost_per_click/cost_per_form 改为 Numeric(18, 2) |

## 修复状态

✅ 已完成 — 2026-04-28
