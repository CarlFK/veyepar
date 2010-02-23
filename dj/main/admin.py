from django.contrib import admin

from main.models import Client, Show, Location, Raw_File, Quality, Episode, Cut_List, State, Log

class ClientAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'name', 'description',)
    list_display_links = ('name',)
    admin_order_field = ('sequence', 'name',)
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Client, ClientAdmin)

class ShowAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'client','name',)
    list_display_links = ('name',)
    admin_order_field = ('sequence', 'name',)
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Show, ShowAdmin)

class LocationAdmin(admin.ModelAdmin):
    list_display = ('id','sequence', 'name','slug')
    list_display_links = ('id',)
    list_editable = ('name','slug')
    admin_order_field = ('sequence', 'name',)
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Location, LocationAdmin)

class Raw_FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'show', 'location', 'start', 'end', ) 
    list_display_links = ('filename',)
    list_filter = ('location',)
    search_fields = ['filename']
admin.site.register(Raw_File, Raw_FileAdmin)

class QualityAdmin(admin.ModelAdmin):
    list_display = ('level', 'name','description')
    admin_order_field = ('level',)
    # list_editable = list_display
admin.site.register(Quality, QualityAdmin)

class EpisodeAdmin(admin.ModelAdmin):
    list_display = (
	'sequence', 'name', 'state', 'show', 'location', 
        'locked','locked_by','start','end',)
    ordering = ('sequence', )
    list_display_links = ('name',)
    list_editable = ('location', 'state','locked','locked_by')
    admin_order_field = ('sequence', 'name',)
    list_filter = ('state','location')
    search_fields = ['name']
    prepopulated_fields = {"slug": ("name",)}
    save_on_top=True
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

