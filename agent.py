import requests
import os
import datetime

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3-coder:30b"

# ── Skills ──────────────────────────────────────────────

def search_web(query: str) -> str:
    return f"搜索结果：关于 '{query}' 的信息（mock）"

def calculate(expression: str) -> str:
    try:
        return str(eval(expression))
    except Exception as e:
        return f"计算错误: {e}"

def read_file(path: str) -> str:
    if os.path.exists(path):
        try:
            return open(path, encoding="utf-8").read()[:3000]
        except Exception as e:
            return f"读取失败: {e}"
    return "文件不存在"

def list_files(directory: str) -> str:
    if os.path.isdir(directory):
        files = os.listdir(directory)
        return "\n".join(files) if files else "目录为空"
    return "目录不存在"

def get_time(_: str) -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

SKILLS = {
    "search":     {"description": "搜索网络信息。参数: 搜索词",           "func": search_web},
    "calculate":  {"description": "执行数学计算。参数: 表达式如 '2+3*4'", "func": calculate},
    "read_file":  {"description": "读取本地文件内容。参数: 文件完整路径",  "func": read_file},
    "list_files": {"description": "列出目录下所有文件。参数: 目录路径",    "func": list_files},
    "get_time":   {"description": "获取当前真实时间。参数: 填任意字符串",  "func": get_time},
}

# ── Prompt ───────────────────────────────────────────────

def build_system_prompt():
    skill_list = "\n".join(
        f"- {name}: {info['description']}" for name, info in SKILLS.items()
    )
    return f"""你是一个智能助手，可以调用以下工具获取真实信息：
{skill_list}

严格遵守以下输出规则：
1. 如果需要调用工具，只输出以下两行，不要输出其他任何内容：
ACTION: 工具名
PARAM: 参数值

2. 只有在拿到工具结果之后，才能输出最终答案，格式：
FINAL: 你的答案

3. 禁止在同一次回复中同时出现 ACTION 和 FINAL。
4. 禁止编造工具结果，必须先调用工具获取真实数据。"""

# ── 解析模型输出 ──────────────────────────────────────────

def parse_response(response: str):
    """
    返回 ("action", action, param) 或 ("final", answer) 或 ("text", text)
    """
    lines = [l.strip() for l in response.strip().splitlines() if l.strip()]

    action = param = None
    final = None

    for line in lines:
        if line.startswith("ACTION:"):
            action = line.removeprefix("ACTION:").strip()
        elif line.startswith("PARAM:"):
            param = line.removeprefix("PARAM:").strip()
        elif line.startswith("FINAL:"):
            final = line.removeprefix("FINAL:").strip()

    # 修复：同时有 ACTION 和 FINAL 时，优先执行 ACTION
    if action:
        return ("action", action, param or "")
    if final:
        return ("final", final)
    return ("text", response.strip())

# ── Agent 主循环 ──────────────────────────────────────────

def call_ollama(messages):
    resp = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.1}   # 低温度让输出更稳定
    })
    resp.raise_for_status()
    return resp.json()["message"]["content"]

def run_agent(user_input: str, max_steps: int = 6):
    print(f"\n{'='*50}")
    print(f"问题: {user_input}")
    print('='*50)

    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user",   "content": user_input},
    ]

    for step in range(max_steps):
        print(f"\n--- 第 {step+1} 步 ---")
        response = call_ollama(messages)
        print(f"模型输出:\n{response}")

        kind, *rest = parse_response(response)

        if kind == "action":
            action, param = rest
            if action in SKILLS:
                result = SKILLS[action]["func"](param)
                print(f"\n✅ 调用 [{action}] 参数: {param}")
                print(f"   结果: {result}")
                # 把工具结果喂回去，明确要求给最终答案
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": f"工具 [{action}] 返回结果：\n{result}\n\n请根据以上结果给出最终答案，格式：FINAL: 你的答案"
                })
            else:
                print(f"\n❌ 未知工具: {action}，可用: {list(SKILLS.keys())}")
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": f"工具 [{action}] 不存在，请从可用工具中选择或直接回答。"
                })

        elif kind == "final":
            answer = rest[0]
            print(f"\n✅ 最终答案: {answer}")
            return answer

        else:  # 直接文本回答
            print(f"\n✅ 直接回答: {rest[0]}")
            return rest[0]

    print("\n⚠️ 达到最大步数限制")
    return "达到最大步数限制"


# ── 入口 ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("🤖 Agent 已启动，输入 'quit' 或 'exit' 退出")
    while True:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "退出"):
            print("再见！")
            break
        run_agent(user_input)