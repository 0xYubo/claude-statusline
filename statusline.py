#!/usr/bin/env python3
"""
Claude Code Statusline 显示脚本
在 Claude Code 底部状态栏显示用量信息
支持从 stdin 读取实时 context 数据，带记忆功能
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

# 缓存文件（保存 context 等会话数据）
CACHE_FILE = Path.home() / ".claude" / "statusline-cache.json"

# ANSI 颜色代码
class Colors:
    # 亮色系
    GREEN = "\033[92m"        # 亮绿
    YELLOW = "\033[93m"       # 亮黄
    RED = "\033[91m"          # 亮红
    CYAN = "\033[96m"         # 亮青
    MAGENTA = "\033[95m"      # 亮紫
    BLUE = "\033[94m"         # 亮蓝
    WHITE = "\033[97m"        # 亮白

    # 进度条颜色（更鲜艳）
    BAR_GREEN = "\033[92m"    # 亮绿
    BAR_YELLOW = "\033[93m"   # 亮黄
    BAR_RED = "\033[91m"      # 亮红
    BAR_CYAN = "\033[96m"     # 亮青
    BAR_BLUE = "\033[94m"     # 亮蓝

    # 样式
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# 配置文件路径
CLAUDE_DIR = Path.home() / ".claude"
STATUS_CACHE = CLAUDE_DIR / "vscode-claude-status-cache.json"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """加载 JSON 文件"""
    try:
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_json(file_path: Path, data: Dict[str, Any]) -> bool:
    """保存 JSON 文件"""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def load_cache() -> Dict[str, Any]:
    """加载缓存数据"""
    return load_json(CACHE_FILE) or {}


def save_cache(cache: Dict[str, Any]) -> bool:
    """保存缓存数据"""
    return save_json(CACHE_FILE, cache)


def read_stdin_json() -> Optional[Dict[str, Any]]:
    """从 stdin 读取 JSON 数据（Claude Code statusline 传入）"""
    try:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            if data:
                return json.loads(data)
    except Exception:
        pass
    return None


def get_context_percentage(stdin_data: Optional[Dict]) -> float:
    """从 stdin 数据中提取 context 使用率，支持多种字段格式"""
    if not stdin_data:
        return 0

    # Claude Code 可能使用不同的字段名格式
    # 尝试 camelCase 和 snake_case
    paths = [
        ["contextWindow", "usedPercentage"],
        ["contextWindow", "used_percentage"],
        ["contextWindow", "used"],
        ["context_window", "usedPercentage"],
        ["context_window", "used_percentage"],
        ["context", "usedPercentage"],
        ["context", "used_percentage"],
    ]

    for path in paths:
        obj = stdin_data
        for key in path:
            if isinstance(obj, dict):
                obj = obj.get(key)
            else:
                obj = None
                break
        if obj is not None:
            try:
                return float(obj)
            except (ValueError, TypeError):
                continue

    # 直接字段
    for key in ["usedPercentage", "used_percentage", "contextUsed", "context_used", "contextPercentage"]:
        val = stdin_data.get(key)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                continue

    return 0


def format_time_remaining(reset_at: Optional[float]) -> str:
    """格式化剩余时间"""
    if not reset_at:
        return "N/A"

    diff = reset_at - time.time()
    if diff <= 0:
        return "✓"

    hours = int(diff // 3600)
    minutes = int((diff % 3600) // 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def get_colored_bar(percentage: float, width: int = 10, use_cyan: bool = False) -> str:
    """生成带颜色的进度条"""
    filled = int(width * percentage / 100)
    empty = width - filled

    # 根据百分比选择颜色
    if percentage >= 90:
        color = Colors.BAR_RED
    elif percentage >= 70:
        color = Colors.BAR_YELLOW
    elif use_cyan:
        color = Colors.BAR_CYAN
    else:
        color = Colors.BAR_GREEN

    bar = f"{color}{'█' * filled}{Colors.DIM}{'░' * empty}{Colors.RESET}"
    return bar


def get_percentage_color(percentage: float) -> str:
    """获取百分比文字颜色"""
    if percentage >= 90:
        return Colors.RED
    elif percentage >= 70:
        return Colors.YELLOW
    else:
        return Colors.GREEN


def get_model_name(settings: Optional[Dict]) -> str:
    """获取模型名称"""
    if settings:
        env = settings.get("env", {})
        model = env.get("ANTHROPIC_MODEL")
        if model:
            return model

        model = settings.get("model")
        if model:
            return model.upper()

    return "Claude"


def main():
    """主函数"""
    # 尝试从 stdin 读取实时数据
    stdin_data = read_stdin_json()

    # 加载配置文件和缓存
    status_cache = load_json(STATUS_CACHE)
    settings = load_json(SETTINGS_FILE)
    cache = load_cache()

    # 获取用量数据
    usage_data = {}
    if status_cache and "usageData" in status_cache:
        usage_data = status_cache["usageData"]

    # 获取 context 使用率（从 stdin）
    context_pct = get_context_percentage(stdin_data)

    # 如果收到有效的 context 数据，更新缓存
    if context_pct > 0:
        cache["last_context_pct"] = context_pct
        cache["last_context_update"] = time.time()
        save_cache(cache)
    else:
        # 使用缓存的值
        cached_pct = cache.get("last_context_pct", 0)
        cached_time = cache.get("last_context_update", 0)
        # 如果缓存不超过 5 分钟，使用缓存值
        if cached_pct > 0 and (time.time() - cached_time) < 300:
            context_pct = cached_pct

    # 计算数值
    util_5h = usage_data.get("utilization5h", 0) * 100
    util_7d = usage_data.get("utilization7d", 0) * 100
    reset_5h = usage_data.get("reset5hAt")
    reset_7d = usage_data.get("reset7dAt")

    # 获取模型
    model = get_model_name(settings)

    # 格式化输出（带颜色）
    bar_ctx = get_colored_bar(context_pct, 10, use_cyan=True)
    bar_5h = get_colored_bar(util_5h, 10)
    bar_7d = get_colored_bar(util_7d, 10)

    pct_ctx_color = get_percentage_color(context_pct)
    pct_5h_color = get_percentage_color(util_5h)
    pct_7d_color = get_percentage_color(util_7d)

    time_5h = format_time_remaining(reset_5h)
    time_7d = format_time_remaining(reset_7d)

    # 状态栏格式
    # [Model] │ Context ████████░░ XX% │ Usage ████████░░ XX% (resets in Xh Xm) │ Weekly ████████░░ XX% (resets in Xh Xm)
    output = (
        f"{Colors.BOLD}{Colors.CYAN}[{model}]{Colors.RESET} │ "
        f"Context {bar_ctx} {pct_ctx_color}{context_pct:.0f}%{Colors.RESET} │ "
        f"Usage {bar_5h} {pct_5h_color}{util_5h:.0f}%{Colors.RESET} "
        f"{Colors.DIM}(resets in {time_5h}){Colors.RESET} │ "
        f"Weekly {bar_7d} {pct_7d_color}{util_7d:.0f}%{Colors.RESET} "
        f"{Colors.DIM}(resets in {time_7d}){Colors.RESET}"
    )

    print(output)


if __name__ == "__main__":
    main()
