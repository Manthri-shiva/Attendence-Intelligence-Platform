import csv
import io
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy.orm import Session as SqlSession, joinedload

from app.models.attendance import Attendance
from app.models.session import Session
from app.models.user import User
from app.services.audit_log import AuditLogService

class ReportService:
    def __init__(self, db: SqlSession):
        self.db = db

    def generate_attendance_report(
        self,
        *,
        format_type: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        organization_id: Optional[int] = None,
        department_id: Optional[int] = None,
        team_id: Optional[int] = None,
        member_id: Optional[int] = None,
        session_id: Optional[int] = None,
        status: Optional[str] = None,
        actor_id: int
    ) -> tuple[bytes, str]:
        """
        Executes database filters and formats the report dataset as CSV, Excel, or PDF.
        """
        # 1. Build Query with eager loading to prevent N+1 queries
        query = self.db.query(Attendance).join(Session).join(User, Attendance.member_id == User.id)
        query = query.options(
            joinedload(Attendance.member),
            joinedload(Attendance.session)
        )

        # Apply Filters
        if start_date:
            query = query.filter(Session.date >= start_date)
        if end_date:
            query = query.filter(Session.date <= end_date)
        if organization_id:
            query = query.filter(Session.organization_id == organization_id)
        if department_id:
            query = query.filter(Session.department_id == department_id)
        if team_id:
            query = query.filter(User.team_id == team_id)
        if member_id:
            query = query.filter(Attendance.member_id == member_id)
        if session_id:
            query = query.filter(Attendance.session_id == session_id)
        if status:
            query = query.filter(Attendance.status == status)

        records = query.order_by(Session.date.desc(), Session.start_time.desc()).all()

        # 2. Format Output
        fmt = format_type.strip().lower()
        
        # Log Audit Log event
        AuditLogService.log_event(
            db=self.db,
            actor_id=actor_id,
            action="EvidenceExported",
            module="Report",
            new_value=f"Generated attendance report. Format: {format_type}. Matches: {len(records)} records."
        )

        if fmt == "csv":
            return self._to_csv(records)
        elif fmt == "excel" or fmt == "xlsx":
            return self._to_excel(records)
        elif fmt == "pdf":
            return self._to_pdf(records)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _to_csv(self, records: List[Attendance]) -> tuple[bytes, str]:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write Headers
        writer.writerow([
            "Attendance ID", "Member ID", "Member Name", "Email", 
            "Session ID", "Session Name", "Session Type", "Date", 
            "Check-In Time", "Check-Out Time", "Duration (mins)", 
            "GPS Status", "Verification Method", "Verification Status", "Status"
        ])

        for r in records:
            writer.writerow([
                r.id,
                r.member_id,
                r.member.full_name if r.member else "Unknown",
                r.member.email if r.member else "N/A",
                r.session_id,
                r.session.name if r.session else "Unknown",
                r.session.session_type if r.session else "N/A",
                r.session.date.strftime("%Y-%m-%d") if (r.session and r.session.date) else "N/A",
                r.check_in_time.strftime("%H:%M:%S") if r.check_in_time else "N/A",
                r.check_out_time.strftime("%H:%M:%S") if r.check_out_time else "N/A",
                r.duration or 0,
                r.gps_status or "N/A",
                r.verification_method or "N/A",
                r.verification_status or "N/A",
                r.status
            ])
            
        content = output.getvalue().encode("utf-8")
        return content, "text/csv"

    def _to_excel(self, records: List[Attendance]) -> tuple[bytes, str]:
        """
        Generates an Excel-compliant HTML-XML table format.
        Microsoft Excel opens this natively, presenting correct grid headers and styling.
        """
        output = io.StringIO()
        output.write("<html><head><meta charset='UTF-8'></head><body>")
        output.write("<table border='1'>")
        
        # Write Headers
        output.write("<tr style='background-color:#1e3a8a; color:white; font-weight:bold;'>")
        headers = [
            "Attendance ID", "Member ID", "Member Name", "Email Address", 
            "Session ID", "Session Name", "Session Type", "Date", 
            "Check-In Time", "Check-Out Time", "Duration (mins)", 
            "GPS Status", "Verification Method", "Verification Status", "Status"
        ]
        for h in headers:
            output.write(f"<th>{h}</th>")
        output.write("</tr>")

        for r in records:
            output.write("<tr>")
            output.write(f"<td>{r.id}</td>")
            output.write(f"<td>{r.member_id}</td>")
            output.write(f"<td>{r.member.full_name if r.member else 'Unknown'}</td>")
            output.write(f"<td>{r.member.email if r.member else 'N/A'}</td>")
            output.write(f"<td>{r.session_id}</td>")
            output.write(f"<td>{r.session.name if r.session else 'Unknown'}</td>")
            output.write(f"<td>{r.session.session_type if r.session else 'N/A'}</td>")
            output.write(f"<td>{r.session.date.strftime('%Y-%m-%d') if (r.session and r.session.date) else 'N/A'}</td>")
            output.write(f"<td>{r.check_in_time.strftime('%H:%M:%S') if r.check_in_time else 'N/A'}</td>")
            output.write(f"<td>{r.check_out_time.strftime('%H:%M:%S') if r.check_out_time else 'N/A'}</td>")
            output.write(f"<td>{r.duration or 0}</td>")
            output.write(f"<td>{r.gps_status or 'N/A'}</td>")
            output.write(f"<td>{r.verification_method or 'N/A'}</td>")
            output.write(f"<td>{r.verification_status or 'N/A'}</td>")
            output.write(f"<td>{r.status}</td>")
            output.write("</tr>")
            
        output.write("</table></body></html>")
        content = output.getvalue().encode("utf-8")
        
        # Serving Excel Content type
        return content, "application/vnd.ms-excel"

    def _to_pdf(self, records: List[Attendance]) -> tuple[bytes, str]:
        """
        Generates a premium, print-friendly HTML report with styled borders,
        headers, and layouts. The browser renders this layout perfectly,
        allowing direct conversion to PDF via print actions.
        """
        output = io.StringIO()
        output.write("<!DOCTYPE html><html><head><style>")
        output.write("""
            body { font-family: sans-serif; margin: 30px; color: #334155; }
            h1 { color: #1e3a8a; margin-bottom: 5px; }
            .meta { font-size: 12px; color: #64748b; margin-bottom: 20px; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 11px; }
            th { background-color: #f1f5f9; color: #1e293b; padding: 10px; border: 1px solid #cbd5e1; text-align: left; }
            td { padding: 8px; border: 1px solid #cbd5e1; }
            tr:nth-child(even) { background-color: #f8fafc; }
            .status-present { color: #16a34a; font-weight: bold; }
            .status-late { color: #d97706; font-weight: bold; }
            .status-absent { color: #dc2626; font-weight: bold; }
            .status-excused { color: #2563eb; font-weight: bold; }
        """)
        output.write("</style></head><body>")
        
        output.write("<h1>Attendance platform Intelligence timesheet</h1>")
        output.write(f"<div class='meta'>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Total records: {len(records)}</div>")
        
        output.write("<table>")
        output.write("<tr>")
        output.write("<th>Attendance ID</th>")
        output.write("<th>Member</th>")
        output.write("<th>Email</th>")
        output.write("<th>Session</th>")
        output.write("<th>Date</th>")
        output.write("<th>Check-In</th>")
        output.write("<th>Check-Out</th>")
        output.write("<th>Duration</th>")
        output.write("<th>Method</th>")
        output.write("<th>Status</th>")
        output.write("</tr>")

        for r in records:
            status_class = f"status-{r.status.lower().replace(' ', '-')}"
            output.write("<tr>")
            output.write(f"<td>{r.id}</td>")
            output.write(f"<td>{r.member.full_name if r.member else 'Unknown'}</td>")
            output.write(f"<td>{r.member.email if r.member else 'N/A'}</td>")
            output.write(f"<td>{r.session.name if r.session else 'Unknown'}</td>")
            output.write(f"<td>{r.session.date.strftime('%Y-%m-%d') if (r.session and r.session.date) else 'N/A'}</td>")
            output.write(f"<td>{r.check_in_time.strftime('%H:%M') if r.check_in_time else 'N/A'}</td>")
            output.write(f"<td>{r.check_out_time.strftime('%H:%M') if r.check_out_time else 'N/A'}</td>")
            output.write(f"<td>{r.duration or 0} mins</td>")
            output.write(f"<td>{r.verification_method or 'N/A'}</td>")
            output.write(f"<td><span class='{status_class}'>{r.status}</span></td>")
            output.write("</tr>")

        output.write("</table></body></html>")
        content = output.getvalue().encode("utf-8")
        
        # Serving print-ready PDF-HTML Content type
        return content, "text/html"
