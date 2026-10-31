# 飞书与 WPS 连接器 — 分页同步（断点续传）+ 权限失败处理

对应 ClawHunt 任务 **#1519**（企业 Agent 系统 32/50｜飞书与 WPS 连接器）。

**验收标准**：提交**配置、分页同步及权限失败处理示例**。

## 一条命令验证全部

```bash
python run_tests.py      # -> PASS 8 / FAIL 0
python demo.py           # -> 分页同步 + 权限跳过演示
```

## 验收三要素（与验收标准逐条对应）

**① 配置路径**
`connectors.py` —— `BaseConnector` 统一抽象 + `FeishuConnector`/
`WpsConnector` 两实现（同一接口：sync/state/save_state/load_state）。

**② 分页同步示例**
游标推进（每页完整落库才推进）、去重（重复 sync 新增 0）、
断点续传（游标保存/恢复，测试 5）。

**③ 权限失败处理示例**
403/无权限文档**跳过并写审计日志**（`permission_denied_skip`），
**不中断整个同步**——飞书样例 2 条无权限文档被跳过，其余 6 条
正常入库（测试 2）。

## 快速开始

```bash
# 零第三方依赖（纯 Python 标准库）
python run_tests.py          # 全部验收验证
python demo.py               # 双连接器同步演示
```

## 目录

```
.
├── connectors.py            # 统一连接器抽象 + 飞书/WPS 实现（核心）
├── run_tests.py             # 验收验证
├── demo.py                  # 双连接器演示
├── docs/（验收对照 / 实现说明 / 验证记录）
├── SETUP.md
└── README.md
```

## 设计要点

1. **统一抽象**：飞书/WPS 同一接口（sync/state/save/load），新增
   平台只需继承 `_page()`。
2. **游标断点续传**：`cursor` 只在页完整处理完后推进；`save_state/
   load_state` 可恢复，不重复不丢失。
3. **权限失败不中断**：无权限文档跳过 + 审计（`skipped_not_aborted`），
   其余文档照常同步——真实企业环境必配行为。
4. **去重**：doc_id 幂等落库，重复同步零新增（测试 4）。
5. **零第三方依赖**：纯标准库 json/os/sys；模拟数据源（脱敏样例），
   真实 API 接入留 adapter。

## 环境

- Python 3.8+
- **零第三方依赖**（纯标准库）

## 边界说明

本单范围 = 连接器的分页同步与权限失败处理（模拟数据源验证）；
真实飞书/WPS API 接入与凭据管理 —— 落地阶段按客户凭据接入。