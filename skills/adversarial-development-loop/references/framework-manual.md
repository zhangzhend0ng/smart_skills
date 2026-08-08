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

- `python scripts/run_meta_bench.py --verify` — 校验全部 manifest schema(必需字段、枚举值、id 唯一、seed 目录命名白名单、fixture.py 存在)。
- `python scripts/run_meta_bench.py --list` — 列出全部种子。
- `python scripts/run_meta_bench.py --score <seed-id> <报告文件> [--json]` — 用对抗 REFUTE 产出的报告评分单种子(判据见下)。
- `python scripts/run_meta_bench.py --score-all <报告目录> [--json]` — **本地回流工作流的基线命令**:对全部种子评分。报告文件名为 `<seed-id 的 '/'→'_'>.md`(如 `scoring-detection_01-false-perfect.md`);缺报告 = MISSING(基准不完整 → FAIL);汇总 `X/Y passed, W failed, Z missing`;`--json` 输出每种子 `status`(pass|fail|missing)。
- `python scripts/new_seed.py <domain> <name> <flaw_type> [--severity s]` — 脚手架新种子(**写模式,工具链唯一写入口**)。自动编号 NN、命名白名单 `[a-z0-9-]`、不覆盖已有目录、拒绝同 domain 重名;`expected_keywords`/`description` 留占位——**语义蒸馏须人/agent 完成**,未完成种子 `--verify` 会响亮 FAIL(有意的门)。
  - 默认 severity 映射(映射键集 == 枚举集,有断言守护):`blocker` = false-perfect / false-worst / degenerate-zero;`major` = magic-threshold / dead-branch / config-hygiene / stale-doc / symmetry / single-layer-fix;`minor` = none。
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

新种子用脚手架生成:`python scripts/new_seed.py <domain> <name> <flaw_type>`(见 §3)——自动编号、命名白名单、占位语义字段;再填入缺陷与关键词/描述。加完跑 `python scripts/run_meta_bench.py --verify`。领域特化指南(如需)放 `references/domain-<name>.md`(一级扁平,遵循 AgentSkills one-level 规则)。

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

## 6. 机械 gate(提交门禁)

`scripts/gate.sh` 只拦"有没有走框架"的**机械事实**,不判语义质量:

- **G1 journal 覆盖**:代码/内核改动(CODE ∪ KERNEL 模式)必须伴随 journal 改动
- **G2 journal 完成标志**:journal 内容必须含合法 `Pattern Index 更新: (N/A|新增)` 行
- **G3 内核/bench 资产改动**:必须通过 meta-bench `--verify` + `--demo`(只读)
- **G4 LF 卫生**:改动集内 `.py`/`.sh` 含 CRLF → FAIL(工作树 pre-commit 检测;CI 快照恒 LF 无意义)

**iter 119 边界(硬约束)**:gate 只查"可由独立观察者复核的过程痕迹"(改动集 / marker 存在性 / bench 退出码),**禁止追加语义检查**——语义级防漂移脚本(check_drift.py 那一类)已被 iter 119 证伪(Stratum loop-journal.md:5297:脚本防不了语义漂移,靠 Pattern Index + 强制 grep + REFUTE 对抗核实)。语义质量靠对抗,不靠 gate。

用法:

```bash
bash scripts/gate.sh            # exit 0=过;1=任一 FAIL;2=环境错误
bash scripts/gate.sh --why      # 打印检查说明
# pre-commit 钩子(可选):ln -s ../../skills/adversarial-development-loop/scripts/gate.sh .git/hooks/pre-commit
```

配置(env 覆盖,默认见脚本头):`GATE_CODE_PATTERNS` / `GATE_KERNEL_PATTERNS` / `GATE_BENCH_PATTERNS` / `GATE_JOURNAL` / `GATE_META_BENCH_CMD`。

**已知宽松语义(对抗审查 M2 接受并文档化)**:G2 只要求 journal 文件含 ≥1 条合法 marker,不校验"哪条 marker 对应哪次改动"——那是语义事实,超出机械边界。

**CI 分工**:CI(`.github/workflows/ci.yml` → `scripts/ci_check.sh`)只跑 primitive——`--verify` + `--demo`(全种子 pass/fail 对)+ `py_compile`;**不调 gate.sh**(CI 快照无工作树改动,gate 恒绿空转,对抗 M3)。**全种子 `--score` 基准属本地回流工作流**(需真实 REFUTE 报告,CI 无报告源),见 §7。

## 7. 真实样本回流(DOGFOOD → 种子候选)

把真实使用中抓到的缺陷类沉淀为 meta-bench 种子,让套件随使用成长(否则永远是静态 8 个):

1. **捕获**:真实任务的 REFUTE 报告抓到某缺陷类(如"配置键覆盖优先级未定义")。
2. **蒸馏**(人/agent,非自动化):抽最小自包含 fixture + 归类 flaw_type + 写关键词/描述。**语义蒸馏是 iter 119 边界——不得自动化**。
3. **脚手架**:`python scripts/new_seed.py <domain> <name> <flaw_type>` 生成目录与占位文件(写模式唯一入口;命名白名单/不覆盖)。
4. **完善**:填 fixture 缺陷 + manifest 关键词/描述。
5. **入册**:`run_meta_bench.py --verify` 必须过;若 `--demo` 报告需同步(循环验证耦合,见 §3 诚实局限),一并更新。

**边界(iter 119)**:脚手架是机械的;语义蒸馏(缺陷归类/关键词/描述)靠人/agent。禁止自动化语义回流。
