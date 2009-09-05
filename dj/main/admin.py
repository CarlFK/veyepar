from django.contrib import admin

from main.models import Client, Show, Location, Raw_File, Quality, Episode, Cut_List, State, Log

class ClientAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'name', 'description',)
    admin_order_field = ('sequence', 'name',)
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Client, ClientAdmin)

class ShowAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'client','name',)
    admin_order_field = ('sequence', 'name',)
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Show, ShowAdmin)

class LocationAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'show', 'name',)
    admin_order_field = ('sequence', 'name',)
    list_filter = ('show',)
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Location, LocationAdmin)

class Raw_FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'location', 'start', 'end', ) 
    # list_display = ('filename', 'location', 'durationhms', 'start', 'end', ) 
    # ordering = ('start',)
admin.site.register(Raw_File, Raw_FileAdmin)

class QualityAdmin(admin.ModelAdmin):
    list_display = ('level', 'name','description')
    admin_order_field = ('level',)
    # list_editable = list_display
admin.site.register(Quality, QualityAdmin)

class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'state', 'location_name', 'start','end','name',)
    ordering = ('sequence', )
    list_display_links = ('name',)
    list_editable = ('sequence', 'state' )
    admin_order_field = ('sequence', 'name',)
    list_filter = ('state','location')
    prepopulated_fields = {"slug": ("name",)}
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

