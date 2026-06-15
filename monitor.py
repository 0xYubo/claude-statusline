#!/usr/bin/env python3
"""
Claude Code 状态监控面板
显示 5h/7d 用量、重置倒计时、模型信息
支持多终端共享数据，可自定义刷新间隔
"""

import json
import time
import os
import sys
import signal
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
except ImportError:
    print("需要安装 rich 库: pip install rich")
    sys.exit(1)

# 配置文件路径
CLAUDE_DIR = Path.home() / ".claude"
STATUS_CACHE = CLAUDE_DIR / "vscode-claude-status-cache.json"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

# 默认刷新间隔（秒）
DEFAULT_REFRESH_INTERVAL = 30

console = Console()


def load_status_cache() -> Optional[Dict[str, Any]]:
    """加载状态缓存文件"""
    try:
        if STATUS_CACHE.exists():
            with open(STATUS_CACHE, "r") as f:
                return json.load(f)
    except Exception as e:
        console.print(f"[yellow]警告: 读取状态缓存失败: {e}[/yellow]")
    return None


def load_settings() -> Optional[Dict[str, Any]]:
    """加载设置文件"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        console.print(f"[yellow]警告: 读取设置失败: {e}[/yellow]")
    return None


def format_reset_time(reset_at: Optional[float]) -> str:
    """格式化重置时间倒计时"""
    if not reset_at:
        return "N/A"

    now = time.time()
    diff = reset_at - now

    if diff <= 0:
        return "[green]已重置[/green]"

    hours = int(diff // 3600)
    minutes = int((diff % 3600) // 60)
    seconds = int(diff % 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def get_usage_color(percentage: float) -> str:
    """根据用量百分比返回颜色"""
    if percentage >= 90:
        return "red"
    elif percentage >= 70:
        return "yellow"
    else:
        return "green"


def create_progress_bar(percentage: float, width: int = 20) -> Text:
    """创建进度条"""
    color = get_usage_color(percentage)
    filled = int(width * percentage / 100)
    empty = width - filled

    bar = Text()
    bar.append("█" * filled, style=f"bold {color}")
    bar.append("░" * empty, style="dim")
    bar.append(f" {percentage:.1f}%", style=f"bold {color}")

    return bar


def get_model_name(settings: Optional[Dict]) -> str:
    """获取当前模型名称"""
    if settings:
        # 优先从环境变量获取
        env = settings.get("env", {})
        model = env.get("ANTHROPIC_MODEL")
        if model:
            return model

        # 从 settings 获取
        model = settings.get("model")
        if model:
            return model.upper()

    return "Unknown"


def build_dashboard(status_cache: Optional[Dict], settings: Optional[Dict]) -> Panel:
    """构建仪表板"""
    usage_data = status_cache.get("usageData", {}) if status_cache else {}
    model_name = get_model_name(settings)

    # 创建主表格
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column("Label", style="bold cyan", width=12)
    table.add_column("Value", min_width=40)

    # 模型信息
    table.add_row("模型", Text(model_name, style="bold magenta"))

    # 5h 用量
    utilization_5h = usage_data.get("utilization5h", 0) * 100
    reset_5h = usage_data.get("reset5hAt")
    table.add_row(
        "5h 用量",
        create_progress_bar(utilization_5h)
    )
    table.add_row(
        "  重置倒计时",
        Text(f"⏱ {format_reset_time(reset_5h)}", style="bold yellow")
    )

    # 分隔线
    table.add_row("", "")

    # 7d 用量
    utilization_7d = usage_data.get("utilization7d", 0) * 100
    reset_7d = usage_data.get("reset7dAt")
    table.add_row(
        "Weekly",
        create_progress_bar(utilization_7d)
    )
    table.add_row(
        "  重置倒计时",
        Text(f"⏱ {format_reset_time(reset_7d)}", style="bold yellow")
    )

    # 状态信息
    limit_status = usage_data.get("limitStatus", "unknown")
    status_style = {
        "allowed": "green",
        "allowed_warning": "yellow",
        "blocked": "red"
    }.get(limit_status, "white")

    table.add_row("", "")
    table.add_row(
        "状态",
        Text(limit_status.upper(), style=f"bold {status_style}")
    )

    # 更新时间
    updated_at = status_cache.get("updatedAt") if status_cache else None
    if updated_at:
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            time_str = updated_at
    else:
        time_str = "N/A"

    table.add_row(
        "更新时间",
        Text(time_str, style="dim")
    )

    # 包装成面板
    return Panel(
        table,
        title="[bold blue]Claude Code 状态监控[/bold blue]",
        subtitle=f"[dim]刷新间隔: {refresh_interval}s | Ctrl+C 退出[/dim]",
        border_style="blue",
        box=box.DOUBLE
    )


def signal_handler(sig, frame):
    """处理 Ctrl+C"""
    console.print("\n[bold green]👋 再见！[/bold green]")
    sys.exit(0)


def main():
    global refresh_interval

    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description="Claude Code 状态监控面板")
    parser.add_argument(
        "-i", "--interval",
        type=int,
        default=DEFAULT_REFRESH_INTERVAL,
        help=f"刷新间隔（秒），默认 {DEFAULT_REFRESH_INTERVAL}"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="只显示一次，不自动刷新"
    )
    args = parser.parse_args()

    refresh_interval = args.interval

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)

    console.print("[bold blue]🚀 Claude Code 状态监控启动[/bold blue]")
    console.print(f"[dim]刷新间隔: {refresh_interval}s | Ctrl+C 退出[/dim]\n")

    with Live(console=console, refresh_per_second=1) as live:
        while True:
            # 加载数据
            status_cache = load_status_cache()
            settings = load_settings()

            # 构建并更新显示
            dashboard = build_dashboard(status_cache, settings)
            live.update(dashboard)

            # 如果只显示一次，退出循环
            if args.once:
                break

            # 等待刷新
            time.sleep(refresh_interval)


if __name__ == "__main__":
    main()
