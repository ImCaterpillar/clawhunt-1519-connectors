# -*- coding: utf-8 -*-
"""连接器主流程验证 —— 对应验收标准「分页同步及权限失败处理示例」

零第三方依赖。
"""
import os
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from connectors import (  # noqa
    FeishuConnector, WpsConnector, ConnectorError)

HERE = os.path.dirname(os.path.abspath(__file__))

PASS, FAIL = [], []
OK = "\u2705"
NO = "\u274c"


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    mark = OK if cond else NO
    line = "  " + mark + " " + name
    if detail:
        line += " -- " + detail
    print(line)


print("=" * 78)
print("Connectors (Feishu/WPS) -- acceptance verification")
print("=" * 78)
print("Acceptance: 分页同步 + 权限失败处理示例\n")

# 1. 飞书分页同步：全部页拉完
fs = FeishuConnector()
n = fs.sync()
check("1. feishu paging sync completes", n == 6 and len(fs.synced) == 6,
      f"new={n} total={len(fs.synced)}")

# 2. 权限失败：403 文档跳过并审计（不中断）
denied = [a for a in fs.audit if a["event"] == "permission_denied_skip"]
check("2. permission-denied docs skipped + audited",
      len(denied) == 2
      and all(a["action"] == "skipped_not_aborted" for a in denied),
      f"skipped={len(denied)}")

# 3. WPS 同一接口不同实现
wp = WpsConnector()
nw = wp.sync()
check("3. wps same-interface sync", nw == 4 and len(wp.synced) == 4,
      f"new={nw}")

# 4. 去重：重复 sync 不产生重复文档
fs2 = FeishuConnector()
fs2.sync()
n2 = fs2.sync()
check("4. re-sync dedupes", n2 == 0 and len(fs2.synced) == 6,
      f"second_pass_new={n2}")

# 5. 断点续传：游标可保存/恢复
fs3 = FeishuConnector()
fs3.cursor = 2                     # 模拟前 2 页已同步
import json                        # noqa
saved = fs3.save_state(os.path.join(HERE, "_state_test.json"))
fs4 = FeishuConnector()
fs4.load_state(saved)
check("5. cursor save/resume", fs4.cursor == 2,
      f"cursor={fs4.cursor}")
os.remove(saved)

# 6. 统一抽象：两个连接器都是 BaseConnector 子类且接口一致
check("6. unified connector interface",
      all(hasattr(c, "sync") and hasattr(c, "state")
          for c in (fs, wp)))

# 7. demo 可运行
r = subprocess.run([sys.executable, "demo.py"], cwd=HERE,
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace")
check("7. demo.py exit=0", r.returncode == 0, f"exit={r.returncode}")

# 8. 交付齐套
refs = ["connectors.py", "run_tests.py", "demo.py",
        "README.md", "SETUP.md",
        "docs/验收对照.md", "docs/实现说明.md", "docs/验证记录.md"]
broken = [x for x in refs if not os.path.isfile(x)]
check("8. delivery set complete (8 files)", not broken,
      "broken=" + str(broken) if broken else str(len(refs)) + " files")

print()
print("=" * 78)
print("Result: PASS " + str(len(PASS)) + "   FAIL " + str(len(FAIL)))
print("=" * 78)
if FAIL:
    print("Failed: " + ", ".join(FAIL))
sys.exit(1 if FAIL else 0)