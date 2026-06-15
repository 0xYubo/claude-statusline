#!/usr/bin/env python3
"""
Claude Code Statusline 显示脚本
在 Claude Code 底部状态栏显示用量信息

数据来源：
- Context: 从 stdin 的 context_window 读取（每个会话独立）
- Usage/Weekly: 从 stdin 的 rate_limits 读取（账号级别，所有会话共享）

多会话共享机制：
rate_limits 不是每次刷新都会传入（仅 API 响应后才有），
因此收到时写入共享缓存文件，未收到时回退读取缓存，
实现所有会话显示一致的账号用量。
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any


# ANSI 颜色代码
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# 共享缓存文件：保存账号级别的 rate_limits，实现多会话同步
CACHE_FILE = Path.home() / ".claude" / "statusline-cache.json"
# 缓存有效期（秒）：超过则视为过期，避免显示陈旧数据
CACHE_TTL = 600


def read_stdin_json() -> Optional[Dict[str, Any]]:
    """从 stdin 读取 Claude Code 传入的 JSON 数据"""
    try:
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            if data:
                return json.loads(data)
    except Exception:
        pass
    return None


def load_cache() -> Dict[str, Any]:
    """加载共享缓存"""
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def save_cache(rate_limits: Dict[str, Any]) -> None:
    """原子写入共享缓存（避免多会话并发写入损坏文件）"""
    try:
        payload = {
            "rate_limits": rate_limits,
            "updated_at": time.time(),
        }
        # 先写临时文件再 rename，保证原子性
        fd, tmp_path = tempfile.mkstemp(dir=str(CACHE_FILE.parent), suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f)
        os.replace(tmp_path, CACHE_FILE)
    except Exception:
        pass


def get_rate_limits(stdin_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取 rate_limits 数据，实现多会话共享：
    - stdin 有数据：使用并更新共享缓存
    - stdin 无数据：回退到共享缓存（其他会话写入的）
    """
    rate_limits = stdin_data.get("rate_limits")

    if rate_limits:
        # 收到实时数据，更新共享缓存供其他会话使用
        save_cache(rate_limits)
        return rate_limits

    # 未收到，尝试读取共享缓存
    cache = load_cache()
    cached = cache.get("rate_limits")
    updated_at = cache.get("updated_at", 0)

    if cached and (time.time() - updated_at) < CACHE_TTL:
        return cached

    return {}


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


def get_colored_bar(percentage: float, width: int = 10, color_type: str = "auto") -> str:
    """生成带颜色的进度条"""
    # 百分比限制在 0-100，避免进度条溢出或为负
    percentage = max(0, min(100, percentage))
    filled = int(width * percentage / 100)
    empty = width - filled

    if percentage >= 90:
        color = Colors.RED
    elif percentage >= 70:
        color = Colors.YELLOW
    elif color_type == "cyan":
        color = Colors.CYAN
    else:
        color = Colors.GREEN

    return f"{color}{'█' * filled}{Colors.DIM}{'░' * empty}{Colors.RESET}"


def get_percentage_color(percentage: float) -> str:
    """获取百分比文字颜色"""
    if percentage >= 90:
        return Colors.RED
    elif percentage >= 70:
        return Colors.YELLOW
    return Colors.GREEN


def main():
    """主函数"""
    stdin_data = read_stdin_json()

    if not stdin_data:
        print("Claude Code")
        return

    # 模型信息
    model_info = stdin_data.get("model", {})
    model_name = model_info.get("display_name") or model_info.get("id") or "Claude"

    # Context 使用率（当前会话独立，stdin 每次都有）
    context_window = stdin_data.get("context_window") or {}
    context_pct = context_window.get("used_percentage") or 0

    # Rate Limits（账号级别，多会话共享）
    rate_limits = get_rate_limits(stdin_data)

    five_hour = rate_limits.get("five_hour") or {}
    util_5h = five_hour.get("used_percentage") or 0
    reset_5h = five_hour.get("resets_at")

    seven_day = rate_limits.get("seven_day") or {}
    util_7d = seven_day.get("used_percentage") or 0
    reset_7d = seven_day.get("resets_at")

    # 进度条
    bar_ctx = get_colored_bar(context_pct, 10, "cyan")
    bar_5h = get_colored_bar(util_5h, 10)
    bar_7d = get_colored_bar(util_7d, 10)

    # 百分比颜色
    pct_ctx_color = get_percentage_color(context_pct)
    pct_5h_color = get_percentage_color(util_5h)
    pct_7d_color = get_percentage_color(util_7d)

    # 重置倒计时
    time_5h = format_time_remaining(reset_5h)
    time_7d = format_time_remaining(reset_7d)

    output = (
        f"{Colors.BOLD}{Colors.CYAN}[{model_name}]{Colors.RESET} │ "
        f"Context {bar_ctx} {pct_ctx_color}{context_pct:.0f}%{Colors.RESET} │ "
        f"Usage {bar_5h} {pct_5h_color}{util_5h:.0f}%{Colors.RESET} "
        f"{Colors.DIM}(resets in {time_5h}){Colors.RESET} │ "
        f"Weekly {bar_7d} {pct_7d_color}{util_7d:.0f}%{Colors.RESET} "
        f"{Colors.DIM}(resets in {time_7d}){Colors.RESET}"
    )

    print(output)


if __name__ == "__main__":
    main()
