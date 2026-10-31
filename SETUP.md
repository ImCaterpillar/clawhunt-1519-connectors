# 设置与运行

零第三方依赖，无需安装任何包。

## 环境要求

- Python 3.8+（标准库：json / os / sys）

## 快速验证

```bash
# 在项目根目录
python run_tests.py        # 验收断言，期望 PASS 8 / FAIL 0
python demo.py             # 双连接器演示，期望退出码 0
```

## 在自己的代码中使用

```python
from connectors import FeishuConnector, WpsConnector

c = FeishuConnector()
n = c.sync()                    # 分页同步（403 自动跳过+审计）
print(n, len(c.synced), c.audit)

# 断点续传：保存/恢复游标
c.save_state("state.json")
c.load_state("state.json")
```

## 接入真实平台

本演示用模拟数据源。接入真实飞书/WPS：
- 继承 `BaseConnector`，把 `_page(idx)` 换成真实 API 分页调用；
- 权限失败路径已内置（跳过+审计），照常生效；
- 凭据管理走环境变量/密钥管理，不写入代码。

## 常见问题

- **无权限文档会中断同步吗？** 不会——跳过并审计（测试 2）。
- **重复同步会重复落库吗？** 不会——doc_id 幂等去重（测试 4）。
- **Windows 中文乱码？** 脚本已内置 UTF-8 重配置。