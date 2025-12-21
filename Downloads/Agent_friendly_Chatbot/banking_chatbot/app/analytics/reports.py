"""
Report Generator for Banking Chatbot Analytics.
Generates daily, weekly, and custom reports.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Report:
    """Generated report."""
    title: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    summary: Dict[str, Any]
    details: Dict[str, Any]
    recommendations: List[str]


class ReportGenerator:
    """
    Generate analytics reports.

    Provides insights and recommendations based on metrics.
    """

    def __init__(self, analytics_data: Dict[str, Any]):
        """
        Initialize with analytics data.

        Args:
            analytics_data: Dictionary containing all analytics metrics
        """
        self.data = analytics_data

    def generate_daily_report(self, date: Optional[datetime] = None) -> Report:
        """Generate daily performance report."""
        if date is None:
            date = datetime.utcnow()

        period_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + timedelta(days=1)

        summary = self._extract_summary()
        details = self._extract_details()
        recommendations = self._generate_recommendations(summary)

        return Report(
            title=f"Daily Report - {date.strftime('%Y-%m-%d')}",
            period_start=period_start,
            period_end=period_end,
            generated_at=datetime.utcnow(),
            summary=summary,
            details=details,
            recommendations=recommendations
        )

    def generate_weekly_report(self) -> Report:
        """Generate weekly performance report."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)

        summary = self._extract_summary()
        details = self._extract_details()
        recommendations = self._generate_recommendations(summary)

        # Add week-over-week comparison
        summary["period"] = "7 days"

        return Report(
            title=f"Weekly Report - Week ending {end_date.strftime('%Y-%m-%d')}",
            period_start=start_date,
            period_end=end_date,
            generated_at=datetime.utcnow(),
            summary=summary,
            details=details,
            recommendations=recommendations
        )

    def _extract_summary(self) -> Dict[str, Any]:
        """Extract summary metrics."""
        return {
            "total_queries": self.data.get("total_queries", 0),
            "avg_confidence": self.data.get("avg_confidence", 0),
            "avg_latency_ms": self.data.get("avg_latency_ms", 0),
            "total_cost_usd": self.data.get("total_cost_usd", 0),
            "escalation_rate": self.data.get("escalation_rate", 0),
            "error_rate": self.data.get("error_rate", 0),
        }

    def _extract_details(self) -> Dict[str, Any]:
        """Extract detailed breakdowns."""
        return {
            "top_intents": self.data.get("intent_breakdown", [])[:10],
            "sentiment_distribution": self.data.get("sentiment_breakdown", {}),
            "hourly_distribution": self.data.get("hourly_distribution", []),
            "latency_percentiles": self.data.get("latency_percentiles", {}),
        }

    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Confidence recommendations
        avg_conf = summary.get("avg_confidence", 0)
        if avg_conf < 0.7:
            recommendations.append(
                f"Low average confidence ({avg_conf:.1%}). Consider:\n"
                "- Adding more training examples for common queries\n"
                "- Improving intent descriptions and key signals\n"
                "- Reviewing frequently misrouted queries"
            )

        # Escalation recommendations
        esc_rate = summary.get("escalation_rate", 0)
        if esc_rate > 15:
            recommendations.append(
                f"High escalation rate ({esc_rate:.1f}%). Consider:\n"
                "- Adding new intents for common escalation triggers\n"
                "- Improving response templates for edge cases\n"
                "- Lowering escalation threshold if too aggressive"
            )

        # Latency recommendations
        latency = summary.get("avg_latency_ms", 0)
        if latency > 2000:
            recommendations.append(
                f"High average latency ({latency:.0f}ms). Consider:\n"
                "- Using faster model (Haiku) for simple queries\n"
                "- Implementing response caching\n"
                "- Optimizing database queries"
            )

        # Cost recommendations
        cost = summary.get("total_cost_usd", 0)
        queries = summary.get("total_queries", 1)
        cost_per_query = cost / max(queries, 1)
        if cost_per_query > 0.01:
            recommendations.append(
                f"High cost per query (${cost_per_query:.4f}). Consider:\n"
                "- Using Haiku for routing, Sonnet only for complex responses\n"
                "- Implementing prompt caching\n"
                "- Reducing max_tokens where possible"
            )

        # Error rate recommendations
        error_rate = summary.get("error_rate", 0)
        if error_rate > 1:
            recommendations.append(
                f"Elevated error rate ({error_rate:.1f}%). Check:\n"
                "- API rate limits and quotas\n"
                "- Network connectivity\n"
                "- Error logs for patterns"
            )

        if not recommendations:
            recommendations.append(
                "All metrics are within healthy ranges. Keep monitoring!"
            )

        return recommendations

    def to_markdown(self, report: Report) -> str:
        """Convert report to markdown format."""
        md = f"""# {report.title}

**Period**: {report.period_start.strftime('%Y-%m-%d %H:%M')} to {report.period_end.strftime('%Y-%m-%d %H:%M')}
**Generated**: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

## Summary

| Metric | Value |
|--------|-------|
| Total Queries | {report.summary['total_queries']:,} |
| Avg Confidence | {report.summary['avg_confidence']:.1%} |
| Avg Latency | {report.summary['avg_latency_ms']:.0f}ms |
| Total Cost | ${report.summary['total_cost_usd']:.4f} |
| Escalation Rate | {report.summary['escalation_rate']:.1f}% |
| Error Rate | {report.summary['error_rate']:.1f}% |

## Top Intents

| Intent | Count |
|--------|-------|
"""
        for intent in report.details.get("top_intents", [])[:5]:
            md += f"| {intent['intent']} | {intent['count']} |\n"

        md += "\n## Recommendations\n\n"
        for i, rec in enumerate(report.recommendations, 1):
            md += f"### {i}. Recommendation\n{rec}\n\n"

        return md

    def to_html(self, report: Report) -> str:
        """Convert report to HTML format."""
        # Simple HTML report
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{report.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 20px; background: #f5f5f5; border-radius: 8px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; }}
        .metric-label {{ color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #4a90d9; color: white; }}
        .recommendation {{ background: #fff3cd; padding: 15px; margin: 10px 0; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>{report.title}</h1>
    <p><strong>Period:</strong> {report.period_start.strftime('%Y-%m-%d')} to {report.period_end.strftime('%Y-%m-%d')}</p>

    <h2>Key Metrics</h2>
    <div class="metrics">
        <div class="metric">
            <div class="metric-value">{report.summary['total_queries']:,}</div>
            <div class="metric-label">Total Queries</div>
        </div>
        <div class="metric">
            <div class="metric-value">{report.summary['avg_confidence']:.1%}</div>
            <div class="metric-label">Avg Confidence</div>
        </div>
        <div class="metric">
            <div class="metric-value">${report.summary['total_cost_usd']:.4f}</div>
            <div class="metric-label">Total Cost</div>
        </div>
        <div class="metric">
            <div class="metric-value">{report.summary['escalation_rate']:.1f}%</div>
            <div class="metric-label">Escalation Rate</div>
        </div>
    </div>

    <h2>Recommendations</h2>
"""
        for rec in report.recommendations:
            html += f'    <div class="recommendation">{rec}</div>\n'

        html += """
</body>
</html>
"""
        return html
