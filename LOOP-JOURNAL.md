# Loop Journal — smart_skills

## 迭代 1 — 将 adversarial-development-loop 重构为标准化框架(对抗修订版)

### 触发的理论缺口
skill 自身无自评测体系;repo 副本(154 行)与 live 版本(397 行)已发散;初版重构计划未核实基底(基于 stale 副本)。

### grep journal 结果(Step 1 强制)
N/A——本仓库首条 journal,Pattern Index 尚无条目。

### 合法 shape 清单 + 覆盖状态(Step 0 产出)
| Shape | 判别字段 | UNDERSTOOD? | 方案覆盖? |
|-------|----------|-------------|-----------|
| zcode 消费 | SKILL.md + agents/openai.yaml(UI manifest) | ✓ | ✓ |
| Claude/其他 AgentSkills 客户端 | SKILL.md + references/scripts/assets | ✓ | ✓ |
| youtu-agent | .agent/skills/ + enabled_skills | 部分(NOT VERIFIED:本环境无证据) | 部分(README 提互操作位置) |
| 领域包插拔 | seeds/<domain>/ 目录模式 + manifest schema | ✓ | ✓ |
| 产物多消费者 | journal schema 单一源 = SKILL.md 模板 | ✓ | ✓ |
| 脚本运行环境 | win32 Git Bash + python3 | python 可用性 NOT VERIFIED | ✓(stdlib-only + 清晰报错) |
| 发行 vs 安装 | repo 权威 + 四副本同步 | ✓ | ✓(安装动作留给用户手动) |

### 退化输入×消费者矩阵(Step 0 产出)
| 退化输入＼组件 | SKILL.md 路由 | run_meta_bench.py | 客户端加载 |
|---|---|---|---|
| 无 python | — | 清晰报错退出 | — |
| manifest 缺字段/类型错 | — | --verify 拦截 | — |
| references 缺失 | 手册指明条件性读取 | — | — |
| description>1024 / name≠目录名 | 校验(name==目录名 ✓) | — | — |
| 新领域包目录深浅不一 | 一级扁平契约(one-level) | — | — |
| CRLF 脚本 | .gitattributes 强制 LF | LF 探测验证 | — |

### 初版方案(被推翻点)
基于 repo 154 行 stale 副本做大规模 references/domains/ 拆分;加 metadata.version、append_journal.sh、meta-bench auto 模式。

### 对抗审查结论([blocker]/[major] 清单)
- [blocker] 基底选错:repo 副本非 live 版本(397 行),重构对 live 零生效且加剧四副本发散
- [blocker] 行号引用全部基于 stale 副本;"零丢失"漏掉 live 版约 240 行核心内容(ENUMERATE/可达性门/逐跳/DOGFOOD/Pattern Index/R1-R4)
- [blocker] 通用分类法(缺口清单/自欺表)误置领域包,抽空内核
- [major] references/domains/ 两级嵌套违反 one-level 规范 / metadata.version 死配置 / 过度拆分(每轮必用内容外置) / meta-bench 评分可游戏化 / 安装被 ~/.zcode shadow / 单层修复自指 / journal schema 多消费者漂移 / CRLF 毒害脚本
- [minor] skill 内 README 反模式 / 描述上限与"<500行"目标悬空等

### 修订方案(逐条 采纳/反驳/backlog)
全部采纳。核心修正:基线换 live 397 行版、repo 为权威发行源、分类法留内核、不拆 reference(仅外置条件性 meta-bench 工具链)、砍 append_journal.sh/auto 模式/metadata.version、评分加干净种子 precision 约束、.gitattributes LF、README 三客户端同步指引(含 shadow 警告)。backlog:无 python fallback 指引;第二领域包模板(YAGNI,等真实领域需求)。

### 数据流 hops 状态
Datum: skill 内容(154 行 repo → 397 行 live 基线)
| Hop | 写者→读者 | 空间 | ✓/✗ |
|-----|-----------|------|-----|
| HOP 1 | .zcode live → repo SKILL.md(基线同步) | 文本内容 | ✓ |
| HOP 2 | repo(发行源)→ README/框架手册同步指引 | 三客户端路径 + shadow | ✓ |
| HOP 3 | 安装副本 = 用户手动执行(未授权不自动写) | 文件系统 | △ |
| HOP 4 | meta-bench 自评测链(seed→report→score) | 评分语义 | ✓ |

### 变种横向 grep 结果(Step 6 强制)
无业务代码变种(本 repo 仅 skill 文件);副本变种已全量枚举(repo/.zcode/.codex/.claude 四份,前 3 份近同 154 行 + .zcode 397 行)。

### 改动文件
skills/adversarial-development-loop/{SKILL.md(基线+速览), agents/openai.yaml, references/framework-manual.md, scripts/run_meta_bench.py, assets/meta-bench/seeds/scoring-detection/{01..07}};.gitattributes;README.md;LOOP-JOURNAL.md

### 测试证据
实测(2026-08-08):meta-bench `--verify` 7/7 manifests valid;`--list` 7 种子;`--demo` 三路自测 OK;`--score` 三路样例报告(命中→PASS / 泛化 blocker 对干净种子→FAIL / 严重级不足→FAIL);全部新增 .py 与 .gitattributes LF 探测 0 CRLF;7 份 manifest `python -m json.tool` 通过;全部 Python `py_compile` 通过;frontmatter name==目录名;repo SKILL.md 对 .zcode 副本 diff 仅 2 处计划内修改(去重标题 + 速览小节),无内容丢失。greenfield 无既有套件,如实说明。

### E2E 证据
--demo 内置三路自测:缺陷种子命中 PASS、干净种子防游戏化 FAIL、严重级不足 FAIL。

### 过程意外 / 与预期偏差
对抗报告实测 .zcode 副本 397 行(初版怀疑"377+");live frontmatter 含 when_to_use 字段(保留——"基线零改动"原则优先,且非 M5 针对的新增字段);repo 工作树 CRLF 需 .gitattributes 兜底;**实现中发现对抗清单外的 bug**:run_meta_bench.py 在 Windows 下 `os.path.join` 产反斜杠 id 与 manifest 正斜杠 id 失配,`--verify` E2E 当场抓到并修复(跨平台路径分隔符,与 CRLF 同类)。另:规划模式自动落盘 `.zcode/plans/plan-sess_*.md`(非本次改动产物,已向用户说明)。

### Pattern Index 更新:新增 meta-bench / skill-copy-divergence / shadow-priority

### 遗留 backlog
无 python 环境 fallback 指引;第二领域包模板(等真实领域出现);安装副本同步由用户手动执行。

---

## 迭代 2 — 审查 REQUEST CHANGES 修复轮

### 触发的理论缺口
对迭代 1 产物做 harness Part B 自审(verdict REQUEST CHANGES),发现:error-handling traceback、eval 数据集缺 out-of-scope 类、评估结果不可结构化聚合、严重级契约未文档化。

### grep journal 结果(Step 1 强制)
Pattern Index(迭代 1):meta-bench / skill-copy-divergence / shadow-priority — 本轮直接复用,无重复坑。

### 合法 shape 清单 + 覆盖状态
| Shape | UNDERSTOOD? | 方案覆盖? |
|-------|-------------|-----------|
| 损坏 manifest 的 CLI 行为 | ✓ | ✓(清晰报错,已 E2E) |
| 评分结果可聚合输出 | ✓ | ✓(--json) |
| out-of-scope 输入的 precision | ✓ | ✓(08-out-of-scope 种子) |
| 严重级契约与文档同步 | ✓ | ✓(manual §3) |

### 对抗审查结论([blocker]/[major] 清单)
(本轮为自审修复,非新方向;对抗审查即迭代 1 的独立对抗 + 本审查报告)

### 修订方案(逐条 采纳/反驳/backlog)
- 采纳 (C) error-handling:cmd_list/cmd_demo 补 try/except → 清晰报错 + exit 1,无 traceback
- 采纳 (C) 数据集组成:新增 08-out-of-scope(纯静态查找表,skill 不适用场景)
- 采纳 (A) `--score --json`:结构化输出便于聚合(对齐 youtu-agent eval 记录思路)
- 采纳 (A) manual §3:严重级括号契约 / 逐种子基准 / 内核改动重跑
- 反驳 (A) 标点统一:基线自身混用半角/全角,统一需动基线,违反"基线零改动"原则 → 不修
- backlog:提交拆分(3 logical unit)、类型标注(接受)、CI 门禁、`--score-all` 批量命令

### 数据流 hops 状态
Datum: 评分结果
| Hop | 写者→读者 | 空间 | ✓/✗ |
|-----|-----------|------|-----|
| HOP 1 | score_report → --score | 评分语义 | ✓ |
| HOP 2 | --score → --json → 聚合者(未来) | JSON | ✓ |

### 变种横向 grep 结果(Step 6 强制)
load_manifest 无保护的调用点共 3 处(cmd_verify 已有 try;cmd_list/cmd_demo 本轮补齐)——同变种已全部扫平。

### 改动文件
run_meta_bench.py(cmd_list/cmd_demo try/except + --json);framework-manual.md §3;新增 08-out-of-scope/{fixture.py,manifest.json};LOOP-JOURNAL.md。

### 测试证据
--verify 8/8;--demo 三路 OK;--score --json 输出合法 JSON(字符串级核实);损坏 manifest → "cannot load manifest ... (run --verify)" exit 1,无 traceback(E2E);py_compile 全通过;新文件 LF 探测 0 CRLF。

### E2E 证据
损坏 manifest 的 `--list` 错误路径实测通过;`--score --json` 输出经 json 解析验证。

### 过程意外 / 与预期偏差
`--list` 对损坏 manifest 的测试首次被 `head -3` 截断误判,单独复跑确认错误消息干净。

### Pattern Index 更新:新增 severity-bracket-contract / eval-json-output

### 遗留 backlog
提交拆分(3 logical unit);类型标注(接受);CI 门禁脚本;`--score-all` 批量命令;真实样本回流(DOGFOOD→种子候选);journal 机械校验。

---

## 迭代 3 — 三条框架修改意见的对抗审查 + 最小落地

### 触发的理论缺口
⑤⑥⑦ 三条建议(REFUTE 指针用法/任务边界契约/契约同步条款)未经对抗直接落 framework-manual 会有双源漂移风险。

### grep journal 结果(Step 1 强制)
Pattern Index(迭代 1-2):meta-bench / skill-copy-divergence / shadow-priority / severity-bracket-contract / eval-json-output;Stratum 实证(:5272 指针、:5296 backlog 漂移、:5276 契约同步)——本轮全部复用。

### 合法 shape 清单 + 覆盖状态
| Shape | UNDERSTOOD? | 方案覆盖? |
|-------|-------------|-----------|
| 执行态规则落 conditional-read 手册 | ✓ | ✓(对抗发现位置错) |
| 与 SKILL.md 模板双源冲突 | ✓ | ✓(改模板本体) |
| 引用数据的一手源核实 | ✓ | ✓(iter 66 伪事实被抓) |

### 对抗审查结论([blocker]/[major] 清单)
- [blocker] ⑤⑥ 落 manual 位置错(manual 日常不读,执行端永不加载)→ 应进 SKILL.md 或砍
- [blocker] ⑤ "iter 66 实测省 60%"伪事实(实为 iter 115 复盘估计,虚拟语气,iter 66 条目无测量)
- [blocker] ⑥ 开局 grep/结尾两步与 Step 1/Step 6 完全重复(减配复述稀释更强规则)
- [major] ⑥ "handoff 被吸收"前提 NOT VERIFIED(handoff-iter25-34 实际覆盖至 iter 41,journal 无吸收记录)
- [major] ⑦ 与 manual §3:50 半重复;iter 89 是代码→文档类推,非直接证据
- [minor] ⑥ "最近 3 轮"与 SKILL.md:123"上一轮"冲突

### 修订方案(逐条 采纳/反驳/backlog)
- 采纳修正 ⑤:SKILL.md 模板一行——短方案粘贴,长/含代码给指针;删伪事实;manual 不加
- 采纳修正 ⑥:整节拒绝;唯一新意(git status 核基线)一句并入 Step 1 首行
- 采纳修正 ⑦:降格为 manual §3:50 半句,点名 §2:38,标注类推
- backlog:⑥ 其余内容(开局 grep/结尾 commit)已由 Step 1/Step 6 覆盖,不新增

### 数据流 hops 状态
N/A(文档契约改动,无跨层 datum;同步点 = SKILL.md 模板/Step 1 ↔ framework-manual §2/§3)

### 变种横向 grep 结果(Step 6 强制)
grep 全文找重复:⑥ 的 grep 仪式/结尾两步 → Step 1(:121-124)/Step 6(:183-189)已覆盖;⑦ → §3:50 已覆盖。同变种(契约双源)已扫平。

### 改动文件
SKILL.md(Step 1 首行 + 对抗模板行);framework-manual.md §3:50;LOOP-JOURNAL.md。

### 测试证据
内核改动后按契约重跑:--verify 8/8、--demo 三路 OK(见验证输出)。

### E2E 证据
grep 编辑区确认落地;LF 探测 0 CRLF;meta-bench 契约重跑通过。

### 过程意外 / 与预期偏差
**自引伪事实**:我在给用户的修改意见里写"iter 66 实测省 ~60% token",对抗核实实为 iter 115 复盘估计(虚拟语气"如果"),iter 66 条目无测量——已修正为"iter 115 复盘结论"。handoff"停更被吸收"前提 NOT VERIFIED(handoff-25-34 覆盖至 iter 41),已从落地内容删除。

### Pattern Index 更新:新增 fact-provenance(引用 iter 数字前核一手源:复盘估计≠实测;iter 66→115 教训)

### 遗留 backlog
提交拆分(3 logical unit);类型标注(接受);CI 门禁脚本;`--score-all`;真实样本回流;journal 机械校验(注意:iter 119 已证伪同类脚本,backlog 内仅作记录不实施)。
