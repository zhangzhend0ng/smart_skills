# smart_skills

标准化 Agent Skills 集合,按 [AgentSkills 开放标准](https://agentskills.io/specification)组织(SKILL.md + references/ + scripts/ + assets/)。

## 布局

```
skills/<name>/SKILL.md
```

每个 skill 遵循 AgentSkills 目录约定:

- `SKILL.md` — 必需;frontmatter(name + description)+ 内核指令
- `references/` — 条件性读取的文档(如框架手册)
- `scripts/` — 可执行工具(如 meta-bench 运行器)
- `assets/` — 静态资源(如 meta-bench 种子夹具)
- `agents/openai.yaml` — zcode/Codex 宿主 UI 界面 manifest(模型不读)

## 当前 skill:adversarial-development-loop

对抗式自循环开发:实现前先由独立审查者证伪方案(ENUMERATE → PLAN → REFUTE → REVISE → 实现(逐跳) → 测试 → 复盘)。

- 内核:见 `skills/adversarial-development-loop/SKILL.md`
- 框架手册(领域包契约/评分规则/安装同步):见 `skills/adversarial-development-loop/references/framework-manual.md`
- 自评测(meta-bench):

```bash
python skills/adversarial-development-loop/scripts/run_meta_bench.py --verify   # 校验种子清单
python skills/adversarial-development-loop/scripts/run_meta_bench.py --list     # 列出种子
python skills/adversarial-development-loop/scripts/run_meta_bench.py --score <seed> <报告文件>  # 评分 REFUTE 检出
python skills/adversarial-development-loop/scripts/run_meta_bench.py --demo     # 内置评分自测
```

**诚实局限**:meta-bench 是 toy 级冒烟测试;manifest 为作者人工标注(存在循环验证),bench 全绿 ≠ skill 有效。详见框架手册 §3。

## 安装 / 同步(发行源 → 客户端)

本仓库是**权威发行源**。各客户端发现优先级不同:**`~/.zcode/skills` 优先级最高,会 shadow 其他位置的同名副本**。

```bash
# zcode(最常用)
cp -r skills/adversarial-development-loop ~/.zcode/skills/
# codex
cp -r skills/adversarial-development-loop ~/.codex/skills/
# claude
cp -r skills/adversarial-development-loop ~/.claude/skills/
# 跨客户端互操作位置(注意:会被 ~/.zcode/skills 同名副本 shadow)
cp -r skills/adversarial-development-loop ~/.agents/skills/
```

⚠️ 装到 `~/.agents/skills` 后若 `~/.zcode/skills` 仍有同名旧副本,zcode 会优先加载旧副本,新版本不生效。同步后验证实际加载版本:

```bash
grep -n "框架结构速览" ~/.zcode/skills/adversarial-development-loop/SKILL.md
```
