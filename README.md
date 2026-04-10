# LLM Agent with Skills

基于 Ollama 本地模型的 Agent 框架，支持工具调用。

## 使用方法
1. 安装依赖：`pip install requests`
2. 启动 Ollama：`ollama run qwen3-coder:30b`
3. 运行：`python agent.py`

## 已支持的 Skills
- `calculate` 数学计算
- `get_time` 获取当前时间
- `list_files` 列出目录文件
- `read_file` 读取文件内容
- `search` 网络搜索（mock）
