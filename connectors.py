# -*- coding: utf-8 -*-
"""飞书/WPS 连接器演示 —— 分页同步（断点续传）+ 权限失败处理

对应 ClawHunt 任务 #1519（企业 Agent 系统 32/50｜飞书与 WPS 连接器），
验收：提交配置、分页同步及权限失败处理示例。

设计（零第三方依赖，模拟数据源不碰真实账号）：
  - Connector：统一连接器抽象（飞书/WPS 两实现，同一接口）
  - 分页同步：游标推进（每页完整落库才推进）、断点续传、去重
  - 权限失败：403/无权限文档跳过并写审计日志，不中断整个同步
  - sync_state.json：同步状态可保存/恢复
"""
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))


class ConnectorError(Exception):
    pass


# ── 模拟数据源（脱敏样例，3 页 × 每页 3-4 条，其中 2 条无权限）──
MOCK_DOCS = {
    "feishu": {
        "pages": [
            [{"doc_id": "fs-001", "title": "差旅政策 v2", "ok": True},
             {"doc_id": "fs-002", "title": "预算口径", "ok": True},
             {"doc_id": "fs-403", "title": "薪酬明细（无权限）", "ok": False}],
            [{"doc_id": "fs-003", "title": "审批矩阵", "ok": True},
             {"doc_id": "fs-004", "title": "SOP 模板", "ok": True},
             {"doc_id": "fs-404", "title": "客户合同（无权限）", "ok": False}],
            [{"doc_id": "fs-005", "title": "评测对照口径", "ok": True},
             {"doc_id": "fs-006", "title": "角色卡索引", "ok": True}],
        ]
    },
    "wps": {
        "pages": [
            [{"doc_id": "wps-001", "title": "经营指标表", "ok": True},
             {"doc_id": "wps-002", "title": "知识条目清单", "ok": True},
             {"doc_id": "wps-403", "title": "财务原始账（无权限）", "ok": False}],
            [{"doc_id": "wps-003", "title": "案例复盘集", "ok": True},
             {"doc_id": "wps-004", "title": "FAQ 汇编", "ok": True}],
        ]
    },
}


class BaseConnector:
    """统一连接器抽象：飞书/WPS 同一接口，分页拉取 + 权限跳过"""

    name = "base"

    def __init__(self):
        self.synced = {}       # doc_id -> doc（去重落库）
        self.cursor = 0        # 游标：只在页完整落库后推进
        self.audit = []        # 权限失败等事件

    def _page(self, page_idx):
        """子类返回该页文档列表（模拟远端）"""
        src = MOCK_DOCS[self.name]["pages"]
        return src[page_idx] if page_idx < len(src) else None

    def sync(self, resume=False):
        """分页同步：游标推进；403 跳过并审计；支持断点续传"""
        if not resume:
            self.cursor = 0
        total_new = 0
        while True:
            page = self._page(self.cursor)
            if page is None:
                break
            page_new = 0
            for doc in page:
                if not doc.get("ok"):
                    self.audit.append({
                        "event": "permission_denied_skip",
                        "doc_id": doc["doc_id"],
                        "title": doc["title"],
                        "action": "skipped_not_aborted",
                    })
                    continue      # 跳过，不中断
                if doc["doc_id"] in self.synced:
                    continue      # 去重
                self.synced[doc["doc_id"]] = doc
                page_new += 1
            # 整页处理完才推进游标（断点续传语义）
            self.cursor += 1
            total_new += page_new
        return total_new

    def state(self):
        return {"cursor": self.cursor, "synced": sorted(self.synced)}

    def save_state(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.state(), f, ensure_ascii=False, indent=1)
        return path

    def load_state(self, path):
        if os.path.isfile(path):
            st = json.load(open(path, encoding="utf-8"))
            self.cursor = st.get("cursor", 0)
        return self.cursor


class FeishuConnector(BaseConnector):
    name = "feishu"


class WpsConnector(BaseConnector):
    name = "wps"


def run_all():
    out = {}
    for cls in (FeishuConnector, WpsConnector):
        c = cls()
        n = c.sync()
        out[cls.name] = {"new_docs": n, "total": len(c.synced),
                         "audit": len(c.audit)}
    return out