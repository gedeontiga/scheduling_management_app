# apps/export/views.py
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.schedule.models import Schedule, ScheduleDay

import weasyprint
from io import BytesIO

class ExportScheduleView(views.APIView):
    """
    API endpoint for exporting a schedule as PDF
    """
    # Fix: Change from class to list
    permission_classes = [IsAuthenticated]
    
    def get(self, request, schedule_id):
        # Get the schedule
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        # Check if user is owner or participant
        if not (schedule.owner == request.user or 
                schedule.participants.filter(user=request.user).exists()):
            return Response(
                {"detail": "You don't have permission to export this schedule"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if schedule is complete
        if not schedule.is_complete:
            return Response(
                {"detail": "Schedule must be complete before exporting"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all days and timeslots for this schedule
        schedule_days = ScheduleDay.objects.filter(
            schedule=schedule
        ).order_by('date')
        
        # Prepare context for template
        context = {
            'schedule': schedule,
            'schedule_days': schedule_days,
            'generated_at': timezone.now(),
            'user': request.user
        }
        
        # Render HTML content using a template
        html_string = render_to_string('schedule_pdf.html', context)
        
        # Generate PDF
        pdf_file = BytesIO()
        weasyprint.HTML(string=html_string).write_pdf(pdf_file)
        pdf_file.seek(0)
        
        # Generate filename
        filename = f"schedule_{schedule.name}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
        filename = filename.replace(' ', '_')
        
        # Create the HTTP response with PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response