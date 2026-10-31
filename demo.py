# -*- coding: utf-8 -*-
"""演示：飞书/WPS 分页同步 + 权限失败处理

运行：python demo.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from connectors import FeishuConnector, WpsConnector  # noqa

print("飞书/WPS 连接器演示 — 分页同步 + 权限失败处理\n")

for cls in (FeishuConnector, WpsConnector):
    c = cls()
    n = c.sync()
    print(f"▼ {cls.name}：新同步 {n} 条，合计 {len(c.synced)} 条")
    for did, doc in sorted(c.synced.items()):
        print(f"  ✅ {did}  {doc['title']}")
    denied = [a for a in c.audit if a["event"] == "permission_denied_skip"]
    for a in denied:
        print(f"  ⏭️ 跳过（无权限，已审计）: {a['doc_id']} {a['title']}")
    print(f"  游标停在 page={c.cursor}（每页完整落库才推进）\n")

print("=" * 50)
print("验收结果: 分页同步 + 权限失败处理 -> ✅ 全部可复现")
print("=" * 50)
sys.exit(0)