# ClawArena OpenClaw 集成 - 快速开始指南

## 🚀 快速开始

### 1. 环境准备
```bash
# 进入项目目录
cd /Users/jacklanda/Desktop/ClawArena

# 激活虚拟环境
source venv/bin/activate

# 验证环境
python --version  # 应该显示 Python 3.10+
openclaw --version  # 应该显示 OpenClaw 版本
```

### 2. 运行优化测试
```bash
# 运行最终优化测试（验证所有改进）
python tests/openclaw/test_final_optimized.py

# 运行 token 计数准确性测试
python tests/openclaw/test_token_accuracy.py

# 运行简单演示
python tests/openclaw/quick_demo.py
```

### 3. 测试 OpenClaw 适配器
```bash
# 测试邮件撰写任务
python tests/openclaw/test_optimized_tasks.py

# 测试货币分析任务（复杂）
python tests/openclaw/test_currency_task.py

# 测试所有任务
python tests/openclaw/test_all_tasks.py
```

## 📋 核心文件说明

### 适配器文件
- `src/clawarena/adapters/builtin/openclaw_adapter_optimized.py` - 优化版 OpenClaw 适配器
- `src/clawarena/adapters/registry_optimized.py` - 优化版注册表

### 任务文件
- `tasks/openclaw/email_composition.yaml` - 邮件撰写任务
- `tasks/openclaw/currency_analysis.yaml` - 货币分析任务（复杂）

### 测试文件
- `tests/openclaw/test_final_optimized.py` - 最终优化验证
- `tests/openclaw/test_token_accuracy.py` - Token 计数测试
- `tests/openclaw/test_currency_task.py` - 复杂任务测试

## 🎯 使用示例

### Python 代码示例
```python
import asyncio
from clawarena.adapters.registry_optimized import optimized_registry
from clawarena.core.task import Task, TaskCategory, TaskDifficulty, EvaluationSpec

# 创建优化适配器
adapter = optimized_registry.get(
    "openclaw-optimized",
    agent_id="main",
    enable_debug=True,
    timeout_seconds=30,
)

# 创建任务
task = Task(
    id="test_task",
    name="Test Task",
    category=TaskCategory("general"),
    difficulty=TaskDifficulty("easy"),
    description="Test task",
    instruction="What is the capital of France?",
    evaluation=EvaluationSpec(evaluator="exact_match", config={}),
    timeout_seconds=60,
)

# 执行任务
response = await adapter.run_task(task)

print(f"Duration: {response.duration_seconds:.2f}s")
print(f"Tokens: {response.token_usage.total_tokens}")
print(f"Response: {response.output}")
```

### 命令行使用
```bash
# 查看可用适配器
python -c "from clawarena.adapters.registry_optimized import optimized_registry; print(optimized_registry.list_available())"

# 查看可用任务
clawarena list tasks

# 运行 OpenClaw 测试
clawarena run --agent openclaw:agent_id=main --category openclaw
```

## 📊 性能指标

### 优化后的性能
- **执行时间**: 5-10秒/任务
- **Token 使用**: 50-200 tokens/任务
- **成本**: $0.0001-$0.0005/任务
- **成功率**: 100% (在测试中)

### 质量指标
- 响应质量显著优于 Dummy 适配器
- 在总结任务上得分高 92.2%
- 生成专业、自然的响应

## 🔧 故障排除

### 常见问题
1. **OpenClaw 命令错误**
   - 确保 OpenClaw 已安装且在 PATH 中
   - 运行 `openclaw --version` 验证

2. **导入错误**
   - 确保在项目根目录运行
   - 确保虚拟环境已激活

3. **Token 计数异常**
   - 优化版适配器会自动检测和纠正
   - 查看调试日志了解详情

### 调试模式
```python
# 启用调试模式查看详细日志
adapter = optimized_registry.get(
    "openclaw-optimized",
    agent_id="main",
    enable_debug=True,  # 启用调试
    timeout_seconds=30,
)
```

## 📚 详细文档

- [OpenClaw 集成指南](docs/OPENCLAW_INTEGRATION.md) - 完整集成说明
- [性能测试报告](docs/PERFORMANCE_REPORT.md) - 详细性能分析
- [项目总结](docs/PROJECT_SUMMARY.md) - 项目概述
- [目录结构](DIRECTORY_STRUCTURE.md) - 完整目录说明

## 🎉 成功标志

如果看到以下输出，说明集成成功：
```
✅ Task completed!
   Duration: 9.93s
   Tokens: 129
   Cost: $0.000193
   Quality: 5/5 checks passed
```

## 🆘 获取帮助

1. 查看详细文档
2. 运行调试脚本：`python tests/debug/debug_tasks.py`
3. 检查 OpenClaw 配置：`openclaw agent --help`

---

*快速开始指南更新时间: 2026年3月22日*  
*作者: Chi (OpenClaw 数字精灵)*