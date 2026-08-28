import logging
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tfc.settings.settings")
logging.disable(logging.CRITICAL)
import django

django.setup()

from tracer.models.project import Project
from tracer.models.trace import Trace, TraceErrorAnalysisStatus
from tracer.models.trace_error_analysis import TraceErrorAnalysis, TraceErrorDetail

project = Project.objects.get(id="a5b0c2b1-aa2a-49c1-b896-2fba4a9121b9")
total_traces = Trace.objects.filter(project=project).count()

statuses = {}
for s in ["PENDING", "PROCESSING", "COMPLETED", "FAILED", "SKIPPED"]:
    val = getattr(TraceErrorAnalysisStatus, s, s)
    count = Trace.objects.filter(project=project, error_analysis_status=val).count()
    if count > 0:
        statuses[s] = count

analyses = TraceErrorAnalysis.objects.filter(project=project).order_by("-analysis_date")

print(f"Project: {project.name}")
print(f"Total traces: {total_traces}")
print(f"Status: {statuses}")
print(f"Total analyses: {analyses.count()}")
print(
    f"Total error details: {TraceErrorDetail.objects.filter(analysis__project=project).count()}"
)
print()
for a in analyses[:15]:
    d = TraceErrorDetail.objects.filter(analysis=a).count()
    print(
        f"  {str(a.trace_id)[:8]}  v={a.agent_version}  errors={a.total_errors}  details={d}  score={a.overall_score}  {a.analysis_date.strftime('%H:%M:%S')}"
    )
