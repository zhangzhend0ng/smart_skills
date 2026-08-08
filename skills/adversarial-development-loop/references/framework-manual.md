# Framework Manual · 框架手册(条件性读取)

> **何时读**:采纳/扩展本框架、新增领域包种子、或同步安装副本时。日常对抗循环执行**不需要**本文件——内核在 `SKILL.md`。

## 1. 内核 vs 领域包边界(不许越界)

- **内核**(`SKILL.md`):7 步循环、ENUMERATE、①½ 可达性门、对抗契约、目标缺口清单(分类法)、诚实性硬原则、迭代元规则 R1-R4、验证纪律、Rationalization Table、Red Flags、Journal 模板、终止条件。
- **分类法禁止迁出内核**:目标缺口清单/自欺表是**领域无关的对抗审查分类法**,任何领域包不得复制或替代;领域包只允许提供**领域特化案例与种子**。
- **领域包**(`assets/meta-bench/seeds/<domain>/`):每个领域一个子目录,承载该领域的 fixture 与预期缺陷标注。

## 2. 领域包插拔契约(manifest schema,一经发布冻结)

种子目录:`assets/meta-bench/seeds/<domain>/<NN>-<name>/`,包含:

- `fixture.py` — 最小自包含的领域代码片段(含种子缺陷,或干净反例)。
- `manifest.json` — 固定字段,机器解析,**禁止改名/改类型**(发布后新增字段可以,改旧字段不行):

```json
{
  "id": "scoring-detection/01-false-perfect",
  "flaw_type": "false-perfect",
  "expected_severity": "blocker",
  "expected_keywords": ["false-perfect", "假满分", "empty input", "无数据"],
  "description": "空输入返回满分 100,把'不可观测'标成'完美一致'。正确做法是无数据时退出总分。"
}
```

字段约束:

| 字段 | 约束 |
|---|---|
| `id` | `<domain>/<NN>-<name>`,全局唯一,与目录路径一致 |
| `flaw_type` | 枚举见下;干净反例用 `none` |
| `expected_severity` | `blocker` / `major` / `minor`;`none` 种子固定为 `minor`(表示"报告不得高于 minor") |
| `expected_keywords` | 字符串数组,**概念级同义词**(评分按子串命中,非精确串) |
| `description` | 人读的缺陷说明(含正确做法,供参考) |

`flaw_type` 枚举(与内核缺口清单对应):`false-perfect`(假满分)/ `false-worst`(假最差)/ `degenerate-zero`(退化零)/ `magic-threshold`(数值无出处)/ `dead-branch`(死代码)/ `config-hygiene`(配置卫生)/ `stale-doc`(文档漂移)/ `symmetry`(对称性)/ `single-layer-fix`(单层修复)/ `none`(干净反例)。

## 3. meta-bench 运行与评分

- `python scripts/run_meta_bench.py --verify` — 校验全部 manifest schema(必需字段、枚举值、id 唯一、fixture.py 存在)。
- `python scripts/run_meta_bench.py --list` — 列出全部种子。
- `python scripts/run_meta_bench.py --score <seed-id> <报告文件> [--json]` — 用对抗 REFUTE 产出的报告评分:
  - **缺陷种子** PASS = 报告**概念级命中**期望缺陷类型(`expected_keywords` 任一同义词子串命中)且严重级 ≥ 期望;
  - **干净种子** PASS = 报告**无 blocker / 无 major**;
  - 对每个种子分别运行 `--score`,**全部 PASS 即本轮基准通过**;
  - 加 `--json` 输出结构化结果(seed/passed/reasons/flaw_type/expected_severity),便于落盘聚合。
- **严重级标记契约**:报告必须用 `[blocker]` / `[major]` / `[minor]` 括号标记每条发现的严重级,评分器据此判定——不标记 = 视为无严重级(缺陷种子必 FAIL)。
- **内核改动后必须重跑**:改动内核(目标缺口清单/评分规则/SKILL.md)后,重跑 `--verify` + `--demo` 并重跑全部种子基准,防内核漂移;同时同步本手册中描述该契约的段落(§2 flaw_type 枚举 / §3 严重级契约——iter 89 类推:代码契约→文档契约)。
- **评分防游戏化**:泛化打 `[blocker]` 的检测器会在干净种子上 FAIL(precision 约束);换措辞不命中 = FAIL(概念匹配,不是字面匹配);严重级不足(如 `[minor]` 报 major 缺陷)= FAIL。
- **诚实局限(必须知情)**:种子是 **toy 级冒烟测试**;manifest 由**同一作者**人工标注,存在**循环验证**(bench 验证的是 REFUTE 对标注种子的检出一致性,不度量 skill 真实质量);bench 全绿 ≠ skill 有效。真实校准(manual 模式人工跑 REFUTE)另行进行,不以本工具替代。

## 4. 新增种子模板

```
assets/meta-bench/seeds/<domain>/<NN>-<name>/
├── fixture.py      # 自包含、可读、<60 行;含一个种子缺陷(或干净反例)
└── manifest.json   # 按第 2 节 schema
```

加完跑 `python scripts/run_meta_bench.py --verify`。领域特化指南(如需)放 `references/domain-<name>.md`(一级扁平,遵循 AgentSkills one-level 规则)。

## 5. 安装与同步(发行源 → 客户端)

本仓库(`smart_skills`)是**权威发行源**。安装副本时注意各客户端发现路径与优先级:

| 客户端 | 安装路径 | 备注 |
|---|---|---|
| zcode | `~/.zcode/skills/adversarial-development-loop/` | **优先级最高**,会 shadow 其他位置同名副本 |
| codex | `~/.codex/skills/adversarial-development-loop/` | |
| claude | `~/.claude/skills/adversarial-development-loop/` | |
| 跨客户端互操作 | `~/.agents/skills/adversarial-development-loop/` | **会被 `~/.zcode/skills` 同名副本 shadow** |

⚠️ **shadow 警告**:装到 `~/.agents/skills` 后,若 `~/.zcode/skills` 仍有同名旧副本,zcode 会优先加载 `.zcode` 旧副本,**新版本不生效**。同步步骤:

1. 复制到目标客户端路径(如 `cp -r skills/adversarial-development-loop ~/.zcode/skills/`);
2. 删除/改名低优先级位置的旧副本;
3. 验证实际加载版本:`grep -n "框架结构速览" ~/.zcode/skills/adversarial-development-loop/SKILL.md`(命中 = 新版本已就位)。
