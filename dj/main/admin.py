from django.contrib import admin

from main.models import Show, Season, Location, Raw_File, Quality, Episode, Cut_List, State, Log

class ShowAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'name',)
    admin_order_field = ('sequence', 'name',)
admin.site.register(Show, ShowAdmin)

class SeasonAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'name',)
    admin_order_field = ('sequence', 'name',)
admin.site.register(Season, SeasonAdmin)

class LocationAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'name',)
    admin_order_field = ('sequence', 'name',)

class Raw_FileAdmin(admin.ModelAdmin):
    list_display = ('filename','start', 'end') 
    admin_order_field = list_display
admin.site.register(Raw_File, Raw_FileAdmin)

class QualityAdmin(admin.ModelAdmin):
    list_display = ('level', 'name',)
    admin_order_field = ('level', 'name',)
    list_editable = list_display
admin.site.register(Quality, QualityAdmin)

class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'name',)
    admin_order_field = ('sequence', 'name',)
admin.site.register(Episode, EpisodeAdmin)

class Cut_ListAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'episode', 'raw_file',)
    admin_order_field = list_display
admin.site.register(Cut_List, Cut_ListAdmin)

class StateAdmin(admin.ModelAdmin):
    list_display = ('slug', 'description',)
    admin_order_field = ('slug', )
admin.site.register(State, StateAdmin)

class LogAdmin(admin.ModelAdmin):
    pass
admin.site.register(Log, LogAdmin)

