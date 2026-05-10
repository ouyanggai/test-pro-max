"""HTML 报告内嵌模板（CSS 单文件）"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: system-ui, -apple-system, 'SF Pro', 'Segoe UI', sans-serif;
         padding: 24px; background: #FFFFFF; color: #1A1D26; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  h1 {{ font-size: 24px; margin-bottom: 24px; color: #1A1D26; }}
  .summary-card {{ background: #FFFFFF; border: 1px solid #E2E4E9;
                   border-radius: 12px; padding: 20px; margin-bottom: 24px;
                   display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .summary-item {{ padding: 8px; }}
  .summary-label {{ font-size: 12px; color: #6B7280; margin-bottom: 4px; }}
  .summary-value {{ font-size: 16px; font-weight: 600; }}
  .branch-tree, .session-log {{ background: #FFFFFF; border: 1px solid #E2E4E9;
                  border-radius: 12px; padding: 16px; margin-bottom: 24px; }}
  .branch-header {{ font-weight: 600; padding: 8px 0;
                    border-bottom: 1px solid #E2E4E9; margin-bottom: 8px; }}
  .node-item {{ padding: 8px 8px 8px 32px; display: flex; justify-content: space-between; }}
  .node-item.completed {{ color: #10B981; }}
  .node-item.failed {{ color: #EF4444; }}
  .node-item.running {{ color: #F59E0B; }}
  .node-item.skipped {{ color: #6B7280; }}
  .log-entry {{ padding: 4px 0; font-size: 13px; color: #6B7280; }}
  .log-entry .action {{ color: #0EA5E9; font-weight: 600; }}
  .sanitized-hint {{ font-size: 12px; color: #6B7280; margin-top: 8px; font-style: italic; }}
</style>
</head>
<body>
<div class="container">
  <h1>{title}</h1>
  <div class="summary-card">{summary_items}</div>
  <div class="branch-tree">
    <div class="branch-header">执行详情</div>
    {branch_details}
  </div>
  <div class="session-log">
    <div class="branch-header">会话日志</div>
    {session_log}
  </div>
  <div class="sanitized-hint">敏感字段已在写入前脱敏</div>
</div>
</body>
</html>"""


def build_summary_item(label: str, value: str) -> str:
    return (
        f'<div class="summary-item">'
        f'<div class="summary-label">{label}</div>'
        f'<div class="summary-value">{value}</div>'
        f'</div>'
    )


def build_node_item(node_name: str, status: str, duration_ms: int) -> str:
    icon_map = {
        "completed": "&#10003;",
        "failed": "&#10007;",
        "running": "&#9679;",
        "skipped": "&#8674;",
        "pending": "&#9675;",
    }
    icon = icon_map.get(status, "&#9675;")
    return (
        f'<div class="node-item {status}">'
        f'{icon} {node_name} <span>{duration_ms}ms</span>'
        f'</div>'
    )


def build_log_entry(timestamp: str, username: str, action: str, reason: str) -> str:
    return (
        f'<div class="log-entry">'
        f'[{timestamp}] <span class="action">{action}</span> '
        f'{username} &#8212; {reason}'
        f'</div>'
    )
