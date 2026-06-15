#!/bin/bash
# Claude Code Wrapper - 自动启动状态监控

# 配置
MONITOR_SCRIPT="/Users/mayubo/Developer/claude-monitor/claude_monitor.py"
MONITOR_PID_FILE="/tmp/claude-monitor.pid"
REFRESH_INTERVAL="${CLAUDE_MONITOR_INTERVAL:-30}"

# 函数：启动 monitor
start_monitor() {
    # 检查是否已经在运行
    if [ -f "$MONITOR_PID_FILE" ]; then
        local old_pid=$(cat "$MONITOR_PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            # 已经在运行，不重复启动
            return 0
        fi
    fi

    # 在后台启动 monitor
    python3 "$MONITOR_SCRIPT" -i "$REFRESH_INTERVAL" > /dev/null 2>&1 &
    local new_pid=$!
    echo "$new_pid" > "$MONITOR_PID_FILE"
}

# 函数：停止 monitor
stop_monitor() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        local pid=$(cat "$MONITOR_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
        fi
        rm -f "$MONITOR_PID_FILE"
    fi
}

# 清理函数
cleanup() {
    stop_monitor
}

# 注册清理函数
trap cleanup EXIT INT TERM

# 启动 monitor
start_monitor

# 执行真正的 claude 命令
/usr/bin/env claude "$@"
