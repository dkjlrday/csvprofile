# csvprofile

**拿到一份 CSV 的头三秒，先搞清楚它长什么样。**

`csvprofile` 读取一个 CSV 文件，输出每一列的类型猜测、缺失率、唯一值数量和高频取值。
它不清洗数据、不修改数据、不做统计分析——只做体检。

- 零依赖，Python 3.10+ 标准库即可运行
- 单文件，`csvprofile.py` 拷走就能用
- 不联网、不写文件

## 为什么需要它

打开一个陌生的 CSV，第一反应通常是打开 Excel 拖两下。但当文件有几百 MB、
编码是 GBK、里面有嵌套引号和换行的时候，Excel 就不好使了。

更常见的情况是：你需要快速判断"这个 `status` 字段有几种取值"、"`amount` 列是不是数字"、
"哪一列缺失得最严重"——这些问题用一次脚本比用眼睛扫十遍快。

```bash
python csvprofile.py data.csv
```

输出：

```
name       整数     缺失     0/5    ( 0.0%)  唯一      3
              · 'ada' × 2
              · 'lin' × 1
              · 'zhou' × 1
age        整数     缺失     1/5   (20.0%)  唯一      2
              · '36' × 1
              · '28' × 1
city       字符串   缺失     0/5    ( 0.0%)  唯一      2
              · 'Beijing' × 2
              · 'Shanghai' × 1
```

一眼能看出：`age` 列混进了空值，`city` 只有两种取值，而 `name` 看起来是主键候选。

## 用法

```bash
# 基本用法
python csvprofile.py data.csv

# 每列多展示几个高频取值
python csvprofile.py data.csv --top 8

# 机器可读输出，方便接进别的工作流
python csvprofile.py data.csv --json
```

JSON 输出的每一列长这样：

```json
{
  "name": "age",
  "type": "integer",
  "total": 5,
  "missing": 1,
  "missing_rate": 0.2,
  "unique": 2,
  "top": [{"value": "36", "count": 1}, {"value": "28", "count": 1}]
}
```

## 类型是怎么猜的

按优先级依次判断，某一列只要**所有非空值**都满足就归为该类型：

| 类型 | 判定规则 |
|---|---|
| `integer` | 每个非空值都能转成 `int` |
| `number` | 每个非空值都能转成 `float`（含整数） |
| `boolean` | 每个非空值属于 `true/false/yes/no/y/n/0/1` |
| `date` | 含 `-` `:` `/` 或年月日，且至少有 4 个数字字符 |
| `string` | 以上都不满足 |
| `empty` | 整列都是空值 |

`0` / `1` 会被同时算作整数和布尔候选——整数优先级更高，所以纯 `0/1` 列会显示成 `integer`。
想要布尔语义，得在下游自己转。

## 已知局限

- **只扫前 100000 行**。更大的文件请先用 `head` 采样，否则统计值会偏。这是为了避免在几 GB 的文件上把内存撑爆。
- **不认 CSV 以外的格式**。Excel 的 `.xlsx`、TSV、Parquet 都不支持——先转成 CSV 再来。
- **编码只处理 UTF-8**（含 BOM）。GBK 文件请先用 `iconv` 转换。
- **日期是"看起来像"，不是"解析成功"**。它不会验证 `2026-13-45` 是不是有效日期。
- **类型判断不跨列**。一列里混着 `1` 和 `abc`，它会整体判为 `string`，不会告诉你混了多少种类型。

## 跑测试

```bash
python test_csvprofile.py
```

测试用独立临时文件，不污染工作目录。

---

## 关于作者

dkjlrday 做数据前先看清数据。这个工具先替你回答「这份 CSV 到底是什么样」，再决定怎么清洗。

- 个人主页：<https://dkjlrday.github.io>
- 仓库：<https://github.com/dkjlrday/csvprofile>

## 许可

MIT，见 [LICENSE](LICENSE)。
