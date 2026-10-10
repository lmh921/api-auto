#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试结果摘要生成器

解析 reports/allure-results 下的 Allure 结果JSON，统计通过/失败/异常/跳过数量，
生成供邮件通知使用的两个文件：
- email_summary.txt  纯文本摘要（邮件正文内嵌）
- email_summary.html 带样式的明细摘要（邮件附件）

用法（Jenkins流水线或本地手动执行）：
    python utils/result_summary.py --results reports/allure-results --out-dir reports --env client-dev
"""
import argparse
import html
import json
from pathlib import Path

FAILURE_STATUSES = ("failed", "broken")
STATUS_NAMES = {"passed": "通过", "failed": "失败", "broken": "异常", "skipped": "跳过", "unknown": "未知"}


def parse_results(results_dir: Path):
    """解析Allure结果文件，返回 (统计字典, 失败用例列表)"""
    stats = {s: 0 for s in STATUS_NAMES}
    failures = []
    starts, stops = [], []

    for file in sorted(results_dir.glob("*-result.json")):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"警告: 无法解析结果文件 {file.name}: {e}")
            continue

        status = data.get("status", "unknown")
        stats[status] = stats.get(status, 0) + 1
        if data.get("start"):
            starts.append(data["start"])
        if data.get("stop"):
            stops.append(data["stop"])

        if status in FAILURE_STATUSES:
            # 失败信息兼容两种字段位置：新版allure-pytest放在statusDetails，旧版放在顶层statusMessage
            details = data.get("statusDetails") or {}
            message = (details.get("message") or data.get("statusMessage") or "").strip().splitlines()
            short_message = " | ".join(part.strip() for part in message[:3])[:300] if message else "(无失败信息)"
            labels = {l.get("name"): l.get("value", "") for l in data.get("labels", [])}
            failures.append({
                "name": data.get("name", file.stem),
                "case_file": labels.get("case_file", ""),
                "status": status,
                "message": short_message,
            })

    duration = ((max(stops) - min(starts)) / 1000) if starts and stops else 0.0
    return stats, failures, duration


def build_txt(env: str, stats: dict, failures: list, duration: float) -> str:
    lines = [
        "接口自动化测试结果",
        f"环境: {env}",
        f"总数: {sum(stats.values())} | " + " | ".join(f"{STATUS_NAMES[k]}: {v}" for k, v in stats.items()),
        f"耗时: {duration:.1f}s",
    ]
    if failures:
        lines.append("")
        lines.append(f"未通过用例 ({len(failures)} 条):")
        for item in failures:
            lines.append(f"  [{STATUS_NAMES[item['status']]}] {item['name']}  ({item['case_file']})")
            lines.append(f"      {item['message']}")
    else:
        lines.append("")
        lines.append("全部用例通过 ✔")
    return "\n".join(lines)


def build_html(env: str, stats: dict, failures: list, duration: float) -> str:
    row = lambda name, value, color: (
        f'<tr><td style="padding:4px 12px;">{name}</td>'
        f'<td style="padding:4px 12px;color:{color};font-weight:bold;">{value}</td></tr>'
    )
    status_colors = {"passed": "#2e7d32", "failed": "#c62828", "broken": "#c62828",
                     "skipped": "#9e9e9e", "unknown": "#9e9e9e"}
    total = sum(stats.values())
    all_pass = not failures

    failure_rows = ""
    for item in failures:
        failure_rows += (
            f'<tr><td style="padding:4px 12px;border-top:1px solid #eee;">'
            f'<span style="color:#c62828;font-weight:bold;">[{STATUS_NAMES[item["status"]]}]</span> '
            f'{html.escape(item["name"])}'
            f'<span style="color:#888;"> ({html.escape(item["case_file"])})</span>'
            f'<div style="color:#555;font-size:12px;white-space:pre-wrap;">{html.escape(item["message"])}</div>'
            f'</td></tr>'
        )

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:'Microsoft YaHei',Arial,sans-serif;font-size:14px;color:#333;">
  <h3 style="margin-bottom:4px;">接口自动化测试结果</h3>
  <div style="color:#888;margin-bottom:12px;">环境: {html.escape(env)} &nbsp;|&nbsp; 耗时: {duration:.1f}s</div>
  <table style="border-collapse:collapse;border:1px solid #ddd;">
    {row("总数", total, "#333")}
    {"".join(row(STATUS_NAMES[k], v, status_colors[k]) for k, v in stats.items())}
  </table>
  <h4 style="margin:16px 0 4px;">{'全部用例通过 ✔' if all_pass else f'未通过用例（{len(failures)} 条）'}</h4>
  <table style="border-collapse:collapse;border:1px solid #ddd;">{failure_rows}</table>
</body></html>
"""


def main():
    parser = argparse.ArgumentParser(description="生成测试结果邮件摘要")
    parser.add_argument("--results", default="reports/allure-results", help="Allure结果目录")
    parser.add_argument("--out-dir", default="reports", help="摘要输出目录")
    parser.add_argument("--env", default="", help="环境名称（仅用于展示）")
    args = parser.parse_args()

    results_dir = Path(args.results)
    if not results_dir.is_dir():
        print(f"错误: 结果目录不存在: {results_dir}")
        raise SystemExit(1)

    stats, failures, duration = parse_results(results_dir)
    total = sum(stats.values())
    if total == 0:
        print(f"错误: {results_dir} 中没有测试结果（pytest是否执行成功？）")
        raise SystemExit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "email_summary.txt").write_text(build_txt(args.env, stats, failures, duration), encoding="utf-8")
    (out_dir / "email_summary.html").write_text(build_html(args.env, stats, failures, duration), encoding="utf-8")

    print(f"SUMMARY: total={total} " + " ".join(f"{k}={v}" for k, v in stats.items()) + f" duration={duration:.1f}s")
    print(f"摘要已生成: {out_dir / 'email_summary.txt'} , {out_dir / 'email_summary.html'}")
    # 存在未通过用例时以退出码1结束，便于流水线感知
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
