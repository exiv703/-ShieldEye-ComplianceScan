import pdfkit
from datetime import datetime
from config import Colors

class Reporter:
    def __init__(self, url, results, scan_duration):
        self.url = url
        self.results = results
        self.scan_duration = scan_duration
        self.report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_html(self):
        all_findings = []
        pages_results = self.results.get('pages', {})
        domain_findings = pages_results.get('domain_findings', {})

        audited_standards = self.results.get('standards', [])

        for category in domain_findings.values():
            all_findings.extend(category)

        for url, page_data in pages_results.items():
            if url == 'domain_findings':
                continue
            for category in page_data.values():
                all_findings.extend(category.get('findings', []))


        unique_findings_messages = set()
        final_findings = []
        for severity, message in all_findings:
            if message not in unique_findings_messages:
                unique_findings_messages.add(message)
                final_findings.append((severity, message))

        severity_map = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'pass': 4}
        final_findings.sort(key=lambda x: severity_map.get(x[0], 99))
        
        summary_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        findings_html = ""
        for severity, message in final_findings:
            if severity != 'pass':
                summary_counts[severity] +=1
                color = self._get_color_for_severity(severity)
                severity_text = severity.upper()
                findings_html += f"""
                <div class="finding {severity}">
                    <span class="severity" style="color: {color};">[{severity_text}]</span>
                    <span class="message">{message}</span>
                </div>
                """
        
        if not findings_html:
            findings_html = f"<p>No violations were found for the audited standards. Congratulations!</p>"

        score = self._calculate_score(summary_counts)
        score_color = self._get_color_for_score(score)

        html = f"""
        <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Helvetica', sans-serif;
                        background-color: {Colors.BACKGROUND_START};
                        color: {Colors.TEXT_MAIN};
                        margin: 40px;
                    }}
                    h1, h2, h3 {{
                        color: {Colors.SECONDARY_ACCENT};
                        border-bottom: 2px solid {Colors.PRIMARY_ACCENT};
                        padding-bottom: 10px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 40px;
                    }}
                    .score-box {{
                        background-color: {score_color};
                        color: {Colors.BUTTON_PRIMARY_TEXT};
                        padding: 20px;
                        margin: 20px auto;
                        border-radius: 10px;
                        width: 150px;
                        text-align: center;
                        font-size: 24px;
                        font-weight: bold;
                    }}
                    .summary-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 30px;
                    }}
                    .summary-table td {{
                        padding: 8px;
                        border: 1px solid {Colors.TEXT_MUTED};
                    }}
                    .finding {{
                        border-left: 5px solid;
                        padding: 10px;
                        margin-bottom: 10px;
                        background-color: #1a2a33;
                        border-radius: 5px;
                    }}
                    .finding.critical {{ border-color: {Colors.DANGER}; }}
                    .finding.high {{ border-color: {Colors.DANGER}; }}
                    .finding.medium {{ border-color: {Colors.WARNING}; }}
                    .finding.low {{ border-color: {Colors.TEXT_MUTED}; }}
                    .severity {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>ShieldEye Security Report</h1>
                    <p>Scan for: {self.url}</p>
                    <p>Date: {self.report_date}</p>
                </div>

                <h2>Overall Security Score</h2>
                <div class="score-box">{score}/100</div>

                <h2>Scan Summary</h2>
                <table class="summary-table">
                    <tr><td>Critical Issues</td><td>{summary_counts['critical']}</td></tr>
                    <tr><td>High Issues</td><td>{summary_counts['high']}</td></tr>
                    <tr><td>Medium Issues</td><td>{summary_counts['medium']}</td></tr>
                    <tr><td>Low Issues</td><td>{summary_counts['low']}</td></tr>
                </table>

                <h3>Scan Details</h3>
                <table class="summary-table">
                    <tr><td>Target URL</td><td>{self.url}</td></tr>
                    <tr><td>Audited Standards</td><td>{', '.join(audited_standards) if audited_standards else 'None'}</td></tr>
                    <tr><td>Scan Duration</td><td>{self.scan_duration:.2f} seconds</td></tr>
                </table>

                <h2>Detailed Findings</h2>
                {findings_html}
            </body>
        </html>
        """
        return html
    
    def generate_pdf(self, output_path):
        html_content = self.generate_html()
        try:
            try:
                pdfkit.from_string("test", False)
            except OSError as e:
                if "No wkhtmltopdf executable found" in str(e):
                     return False, "Required program 'wkhtmltopdf' not found. Please install it and add it to the system path."
                raise e
            
            pdfkit.from_string(html_content, output_path)
            return True, None
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False, f"An unexpected error occurred while generating the report: {e}"

    def _get_color_for_severity(self, severity):
        return {
            'critical': Colors.DANGER,
            'high': Colors.DANGER,
            'medium': Colors.WARNING,
            'low': Colors.TEXT_MUTED
        }.get(severity, Colors.TEXT_MAIN)

    def _calculate_score(self, summary_counts):
        score = 100
        score -= summary_counts['critical'] * 20
        score -= summary_counts['high'] * 10
        score -= summary_counts['medium'] * 5
        score -= summary_counts['low'] * 2
        return max(0, score)

    def _get_color_for_score(self, score):
        if score >= 80:
            return Colors.SUCCESS
        elif score >= 50:
            return Colors.WARNING
        else:
            return Colors.DANGER 