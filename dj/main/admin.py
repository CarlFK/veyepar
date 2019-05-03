from django.contrib import admin
from django.contrib import messages
from django.utils.translation import ungettext

from django import forms
from django.db import models

from main.models import \
        Client, Show, Location, Raw_File, Quality, Episode, \
        Cut_List, State, Log, Image_File, Mark


class ClientAdmin(admin.ModelAdmin):
    list_display = ('active', 'name', 'bucket_id',)
    list_display_links = ('name',)
    list_editable = ('active', )
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
    list_display = ('id','sequence','active', 'name','slug','dirname',)
    list_display_links = ('id',)
    list_editable = ('sequence', 'active', 'dirname','name','slug',)
    search_fields = ['name', ]
    admin_order_field = ('sequence', 'name',)
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ('show', 'active' )
admin.site.register(Location, LocationAdmin)

class Raw_FileAdmin(admin.ModelAdmin):
    list_display = ('id',
            'filename',
    #'show', 'location',
            'start', 'duration', 'end',
            )
    list_editable = ('filename', )
    # list_display_links = ('filename',)
    # list_filter = ('location',"start", "show")
    search_fields = ['filename']
    date_hierarchy = 'start'
admin.site.register(Raw_File, Raw_FileAdmin)

class MarkAdmin(admin.ModelAdmin):
    list_filter = ('location',"click", )
    date_hierarchy = 'click'
    list_display = ('location', 'click',)
admin.site.register(Mark, MarkAdmin)

class Image_FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'show', 'location', )
    list_display_links = ('filename',)
    list_filter = ('location','show', )
    search_fields = ['filename', 'text']
admin.site.register(Image_File, Image_FileAdmin)

class QualityAdmin(admin.ModelAdmin):
    list_display = ('level', 'name','description')
    admin_order_field = ('level',)
    # list_editable = list_display
admin.site.register(Quality, QualityAdmin)

class EpisodeAdmin(admin.ModelAdmin):

    """
    def state_bumper(self,obj):
        return '<input type="submit" value="+" class=pb>'
    state_bumper.allow_tags = True
    state_bumper.short_description = 'bump'
    """

    list_display = (
            # 'id',
            # 'conf_key',
            # 'conf_url',
            # 'state',
            'name',
            'start',
            'end',
            'duration',
            'comment',
            # 'authors',
            # 'emails',
            # 'reviewers',
            # 'twitter_id',
            # 'host_url',
            # 'locked_by',
            # 'location',
            # 'released',
)
    list_editable = (
            # 'state',
            # 'name',
            # 'authors',
            # 'released',
            # 'emails',
            # 'reviewers',
            # 'twitter_id',
            # 'conf_key',
            # 'conf_url',
            # 'sequence',
            'start',
            'end',
            'duration',
            )


	# 'sequence', 'name', 'state', 'state_bumper',
    #     'location',
    #     'locked','locked_by',
    #     'show',
    #     'start','end',)
    # list_display = ( 'sequence', 'name', 'state', 'state_bumper', 'duration' )
    list_display_links = ('name',)
    ordering = ('start', )
    date_hierarchy = 'start'
            # 'locked','locked_by', )
    # list_editable = ('state','duration')
    admin_order_field = ('start', 'name',)
    xlist_filter = ('state','location','locked','locked_by', 'show', 'released')
    search_fields = ['name', 'conf_key']
    prepopulated_fields = {"slug": ("name",)}
    save_on_top=True

    formfield_overrides = {
            models.TextField: {
                'widget': forms.Textarea({'cols': 30, 'rows': 2}),
            }}

    actions = [
            'set_stopped', 'clear_locked', 're_slug',
            'bump_state', 'smack_state',
            'encode_state'] \
            + admin.ModelAdmin.actions

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
    clear_locked.short_discription = "Clear locked timestamp"

    def re_slug(self, request, queryset):
        rows_updated = 0
        for obj in queryset:
            # obj.slug = fnify(obj.name)
            obj.slug = "" ## blank slug, .save will gen a slug.
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
    re_slug.short_discription = "reset slug"

    def bump_state(self, request, queryset):
        rows_updated = 0
        for obj in queryset:
            obj.state += 1
            obj.save()
            rows_updated +=1

        msg = ungettext(
            'bumpped state in %(count)d %(name)s successfully.',
            'bumpped state in %(count)d %(name_plural)s successfully.',
            rows_updated
        ) % {
            'count': rows_updated,
            'name': self.model._meta.verbose_name.title(),
            'name_plural': self.model._meta.verbose_name_plural.title()
        }
        messages.success(request, msg)
    bump_state.short_discription = "bump state"

    def smack_state(self, request, queryset):
        rows_updated = 0
        for obj in queryset:
            obj.state -= 1
            obj.save()
            rows_updated +=1

        msg = ungettext(
            'smacked state in %(count)d %(name)s successfully.',
            'smacked state in %(count)d %(name_plural)s successfully.',
            rows_updated
        ) % {
            'count': rows_updated,
            'name': self.model._meta.verbose_name.title(),
            'name_plural': self.model._meta.verbose_name_plural.title()
        }
        messages.success(request, msg)
    bump_state.short_discription = "smacke state back a notch"


    def encode_state(self, request, queryset):
        rows_updated = 0
        for obj in queryset:
            obj.state = 2
            obj.save()
            rows_updated +=1

        msg = ungettext(
            'set state in %(count)d %(name)s to 2-Encode.',
            'set state in %(count)d %(name_plural)s to 2-Enocde.',
            rows_updated
        ) % {
            'count': rows_updated,
            'name': self.model._meta.verbose_name.title(),
            'name_plural': self.model._meta.verbose_name_plural.title()
        }
        messages.success(request, msg)
    encode_state.short_discription = "set to encode"


    class Media:
        js = ("/static/js/jquery.js","/static/js/bumpbut.js",)
admin.site.register(Episode, EpisodeAdmin)

class Cut_ListAdmin(admin.ModelAdmin):
    list_display = ('sequence', 'apply', 'episode', 'start','end', 'raw_file',)
    list_editable = ('apply', 'start', 'end',)
    list_filter = ('episode__show','episode__location')
    # date_hierarchy = 'episode__start'

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

