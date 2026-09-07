# market-holidays-cdn

A 股 / 美股非交易日日历，通过 jsDelivr 分发，供 iPhone 日历订阅后配合快捷指令实现「只在交易日提醒开盘」。

## 文件

| 文件 | 内容 | 事件数 |
|---|---|---|
| `cn-market-closed.ics` | A股非交易日 = 法定休市 + 全部周末 | 123 |
| `cn-holidays-only.ics` | A股法定休市（仅工作日，精简版） | 19 |
| `us-market-closed.ics` | 美股非交易日 = NYSE 休市 + 全部周末（2026–2030） | 571 |
| `us-early-close.ics` | 美股提前收盘日（当天仍开盘，美东 13:00 收） | 8 |

## 订阅链接

把下面的 `OWNER` / `REPO` 换成你自己的 GitHub 用户名和仓库名：

```
webcal://cdn.jsdelivr.net/gh/OWNER/REPO@main/cn-market-closed.ics
webcal://cdn.jsdelivr.net/gh/OWNER/REPO@main/us-market-closed.ics
webcal://cdn.jsdelivr.net/gh/OWNER/REPO@main/us-early-close.ics
```

若 iPhone 不认 `webcal://`，把前缀换成 `https://` 再试一次，两者等价。

## 数据来源

- **A 股**：沪深北交易所年度《节假日休市安排》通知，人工录入 `CN_CLOSED_RANGES`。次年安排一般 11–12 月公布。
- **美股**：按 NYSE 规则算法生成（`nyse_holidays`），已用 2026–2029 官方数据逐条校验：
  - 元旦（落周日补 1/2，落周六不补）
  - MLK = 1 月第 3 个周一
  - 总统日 = 2 月第 3 个周一
  - 耶稣受难日 = 复活节前两天（Anonymous Gregorian 算法）
  - 阵亡将士纪念日 = 5 月最后一个周一
  - 六月节 6/19（周末调休）
  - 独立日 7/4（周末调休）
  - 劳动节 = 9 月第 1 个周一
  - 感恩节 = 11 月第 4 个周四
  - 圣诞节 12/25（周末调休）

验证：2026 = 251 个交易日，2027 = 251，2028 = 251，与 NYSE 公布一致。

## 自动更新

`.github/workflows/update.yml`：每月 1 号重跑 `build_ics.py`，有变化就自动提交并刷新 jsDelivr 缓存；每年 12 月 1 号额外开一个 issue 提醒补 A 股次年数据。

仓库需为 **Public**，jsDelivr 才能读取。

## 本地重新生成

```bash
python build_ics.py
```

无第三方依赖，标准库即可。
