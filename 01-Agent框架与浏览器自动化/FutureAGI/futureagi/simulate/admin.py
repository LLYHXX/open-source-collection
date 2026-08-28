# from django.contrib import admin
# from .models import  AgentDefinition, SimulateEvalConfig, Persona

# # Register your models here.
# # admin.site.register(Scenarios)
# admin.site.register(AgentDefinition)


# @admin.register(SimulatorAgent)
# class SimulatorAgentAdmin(admin.ModelAdmin):
#     list_display = ["id", "name", "organization", "created_at"]
#     list_filter = ["organization", "created_at"]
#     search_fields = ["name", "prompt"]
#     readonly_fields = ["id", "created_at", "updated_at"]


# @admin.register(SimulateEvalConfig)
# class SimulateEvalConfigAdmin(admin.ModelAdmin):
#     list_display = ["id", "name", "status", "created_at"]
#     list_filter = ["status", "created_at"]
#     search_fields = ["name"]
#     readonly_fields = ["id", "created_at", "updated_at"]


# @admin.register(RunTest)
# class RunTestAdmin(admin.ModelAdmin):
#     list_display = [
#         "name",
#         "agent_definition",
#         "simulator_agent",
#         "organization",
#         "created_at",
#     ]
#     list_filter = ["organization", "created_at"]
#     search_fields = ["name", "agent_definition__agent_name", "simulator_agent__name"]
#     filter_horizontal = ["scenarios"]
#     readonly_fields = ["id", "created_at", "updated_at"]

#     fieldsets = (
#         ("Basic Information", {"fields": ("id", "name", "organization")}),
#         (
#             "Configuration",
#             {
#                 "fields": (
#                     "agent_definition",
#                     "simulator_agent",
#                     "scenarios",
#                     "dataset_row_ids",
#                 )
#             },
#         ),
#         (
#             "Timestamps",
#             {"fields": ("created_at", "updated_at", "deleted", "deleted_at")},
#         ),
#     )


# @admin.register(Persona)
# class PersonaAdmin(admin.ModelAdmin):
#     list_display = ['name', 'persona_type', 'gender', 'age_group', 'occupation', 'organization', 'workspace', 'is_default', 'created_at']
#     list_filter = ['persona_type', 'gender', 'is_default', 'organization', 'created_at']
#     search_fields = ['name', 'description', 'keywords']
#     readonly_fields = ['id', 'created_at', 'updated_at']

#     fieldsets = (
#         ('Basic Information', {
#             'fields': ('id', 'persona_type', 'name', 'description', 'is_default')
#         }),
#         ('Organization & Workspace', {
#             'fields': ('organization', 'workspace')
#         }),
#         ('Demographics', {
#             'fields': ('gender', 'age_group', 'occupation', 'location')
#         }),
#         ('Behavioral Profile', {
#             'fields': ('personality', 'communication_style')
#         }),
#         ('Speech Profile', {
#             'fields': ('multilingual', 'languages', 'accent', 'conversation_speed')
#         }),
#         ('Advanced Settings', {
#             'fields': ('background_sound', 'finished_speaking_sensitivity', 'interrupt_sensitivity')
#         }),
#         ('Additional Data', {
#             'fields': ('keywords', 'metadata'),
#             'classes': ('collapse',)
#         }),
#         ('Timestamps', {
#             'fields': ('created_at', 'updated_at', 'deleted', 'deleted_at'),
#             'classes': ('collapse',)
#         }),
#     )

#     def get_queryset(self, request):
#         """Override to use no_workspace_objects for admin to see all personas"""
#         return Persona.no_workspace_objects.all()
