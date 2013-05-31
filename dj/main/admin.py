from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ungettext

from main.models import Client, Show, Location, Raw_File, Quality, Episode, Cut_List, State, Log, fnify

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
    list_display = ('id','sequence', 'active', 'name','slug')
    list_display_links = ('id',)
    list_editable = ('sequence', 'active', 'name','slug')
    admin_order_field = ('sequence', 'name',)
    prepopulated_fields = {"slug": ("name",)}
admin.site.register(Location, LocationAdmin)

class Raw_FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'show', 'location', 'start', 'duration', 'end', ) 
    list_display_links = ('filename',)
    list_filter = ('location',)
    search_fields = ['filename']
    date_hierarchy = 'start'
admin.site.register(Raw_File, Raw_FileAdmin)

class QualityAdmin(admin.ModelAdmin):
    list_display = ('level', 'name','description')
    admin_order_field = ('level',)
    # list_editable = list_display
admin.site.register(Quality, QualityAdmin)

class EpisodeAdmin(admin.ModelAdmin):

    def state_bumper(self,obj):
        return '<input type="submit" value="+" class=pb>' 
    state_bumper.allow_tags = True
    state_bumper.short_description = 'bump'

    list_display = ('id',
            'state',
            'name', 
            'archive_mp4_url',
            'host_url',
)

       
	# 'sequence', 'name', 'state', 'state_bumper', 
    #     'location', 
    #     'locked','locked_by',
    #     'show', 
    #     'start','end',)
    # list_display = ( 'sequence', 'name', 'state', 'state_bumper', 'duration' )
    list_display_links = ('id',)
    # list_editable = ('start',)
    ordering = ('sequence', )
    date_hierarchy = 'start'
            # 'locked','locked_by', )
    # list_editable = ('state','duration')
    admin_order_field = ('sequence', 'name',)
    list_filter = ('state','location','locked','locked_by', 'show', 'released')
    search_fields = ['name']
    prepopulated_fields = {"slug": ("name",)}
    save_on_top=True
    actions = ['set_stopped', 'clear_locked', 're_slug' ] + admin.ModelAdmin.actions

    def set_stopped(self, request, queryset):
        rows_updated = queryset.update(stop=True)
        msg = ungettext(
            'Set stopped to true in %(count)d %(name)s successfully.',
            'Set stopped to true in %(count)d %(name_plural)s successfully.',
            rows_updated
        ) % {
            'count': rows_updated,
            'name': self.model._meta.verbose_name.title(),
            'name_plural': self.model._meta.verbose_name_plural.title()
        }
        messages.success(request, msg)
    set_stopped.short_discription = "Set stop"

    def clear_locked(self, request, queryset):
        rows_updated = queryset.update(locked=None)
        msg = ungettext(
            'Cleared locked timestamp in %(count)d %(name)s successfully.',
            'Cleared locked timestamp in %(count)d %(name_plural)s successfully.',
            rows_updated
        ) % {
            'count': rows_updated,
            'name': self.model._meta.verbose_name.title(),
            'name_plural': self.model._meta.verbose_name_plural.title()
        }
        messages.success(request, msg)
    set_stopped.short_discription = "Clear locked timestamp"

    def re_slug(self, request, queryset):
        rows_updated = 0
        for obj in queryset:
            obj.slug = fnify(obj.name)
            obj.save()
            rows_updated +=1

        msg = ungettext(
            'updated slug with fnify(name) in %(count)d %(name)s successfully.',
            'updated slug with fnify(name) in %(count)d %(name_plural)s successfully.',
            rows_updated
        ) % {
            'count': rows_updated,
            'name': self.model._meta.verbose_name.title(),
            'name_plural': self.model._meta.verbose_name_plural.title()
        }
        messages.success(request, msg)
    set_stopped.short_discription = "reset slug"

    class Media:
        js = ("/static/js/jquery.js","/static/js/bumpbut.js",)
admin.site.register(Episode, EpisodeAdmin)

class Cut_ListAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'episode', 'apply', 'raw_file',)
    list_editable = ('apply',)
    list_filter = ('episode__show',)
    admin_order_field = list_display

    actions = ['un_apply' ] + admin.ModelAdmin.actions
    def un_apply(self, request, queryset):
        rows_updated = queryset.update(apply=False)
        msg = ungettext(
            'Cleared Apply in %(count)d %(name)s successfully.',
            'Cleared Apply in %(count)d %(name_plural)s successfully.',
            rows_updated
        ) % {
            'count': rows_updated,
            'name': self.model._meta.verbose_name.title(),
            'name_plural': self.model._meta.verbose_name_plural.title()
        }
        messages.success(request, msg)
    un_apply.short_discription = "Un-Apply All"

admin.site.register(Cut_List, Cut_ListAdmin)

class StateAdmin(admin.ModelAdmin):
    list_display = ('sequence','slug', 'description',)
    admin_order_field = ('sequence', )
admin.site.register(State, StateAdmin)

class LogAdmin(admin.ModelAdmin):
    list_display=['episode', 'state', 'start', 'end', 'duration']
    list_display_links = ('episode',)
admin.site.register(Log, LogAdmin)

