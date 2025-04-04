from rest_framework import serializers
from apps.users.serializers import UserSerializer
from apps.schedule.models import Schedule, Role, Participant, ScheduleDay, TimeSlot, PermutationRequest

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'can_edit_schedule', 'can_invate_users', 'can_request_permutations']
        read_only_fields = ['id']
        
class ScheduleSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Schedule
        fields = [
            'id', 'name', 'description', 'owner', 'created_at', 'updated_at', 
            'duration', 'available_days', 'is_complete', 'min_days_required',
            'user_specific_requirements', 'roles', 'to_weeks', 'to_months', 'to_years'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'to_weeks', 'to_months', 'to_years']
        
class ParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    role = RoleSerializer(read_only=True)

    class Meta:
        model = Participant
        fields = ['id', 'user', 'role', 'joined_at', 'invitation_accepted']
        read_only_fields = ['id', 'user', 'joined_at']
        
class TimeSlotSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'start_time', 'end_time', 'participants', 'is_available', 'has_alarm', 'alarm_times', 'last_modified', 'sync_status']
        read_only_fields = ['id', 'last_modified']
        
class ScheduleDaySerializer(serializers.ModelSerializer):
    time_slots = TimeSlotSerializer(many=True, read_only=True)
    
    class Meta:
        model = ScheduleDay
        fields = ['id', 'date', 'time_slots']
        read_only_fields = ['id']
        
class PermutationRequestSerializer(serializers.ModelSerializer):
    requester = ParticipantSerializer(read_only=True)
    recipient = ParticipantSerializer(read_only=True)
    requester_slot = TimeSlotSerializer(read_only=True)
    recipient_slot = TimeSlotSerializer(read_only=True)
    
    class Meta:
        model = PermutationRequest
        fields = ['id', 'requester', 'recipient', 'requester_slot', 'recipient_slot', 'message', 'created_at', 'status']
        read_only_fields = ['id', 'created_at']