from django.contrib import admin
from .models import User, Company, Service, Notification

# CSV imoprt
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from django.contrib.auth.hashers import make_password

"""
CSVのインポート・エクスポート
"""
class UserResource(resources.ModelResource):

    def before_import_row(self,row, **kwargs):
        value = row['password']
        row['password'] = make_password(value)

    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = User
        skip_unchanged = True
        report_skipped = False
        import_id_fields = ('id', 'last_login', 'is_superuser', 'is_active', 'is_staff', 'is_activate', 'display_name', 'email', 'last_name', 'middle_name', 'first_name', 'description', 'created_date')



# Register your models here.
# class UserAdmin(admin.ModelAdmin):
class UserAdmin(ImportExportModelAdmin):

    list_display = ('id', 'last_login', 'is_superuser', 'is_active', 'is_staff', 'is_activate', 'display_name', 'email', 'last_name', 'middle_name', 'first_name', 'description', 'created_date', '_service_admin', 'company')
    list_display_links = ('id',)

    # def _group(self, row):
    #     return ','.join([x.name for x in row.group.all()])

    def _service_admin(self, row):
        print("あああああああああああああああ", row)
        return ','.join([x.name for x in row.service_admin.all()])


    resource_class = UserResource


class CompanyAdmin(ImportExportModelAdmin):
    list_display = ('id', 'pic_company_name', 'pic_dept_name', 'pic_full_name', 'pic_post_code', 'pic_address', 'pic_tel_number', )
    list_display_links = ('pic_company_name', 'pic_dept_name', 'pic_full_name', 'pic_post_code', 'pic_address', 'pic_tel_number', )

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'initial', 'icon', 'number')
    list_display_links = ('name', 'description')


class NotificationAdmin(admin.ModelAdmin):
    # list_display = ('id', 'release_date', 'title', 'category', 'target_user', 'is_read')
    list_display = ('id', 'release_date', 'title', 'category', 'target_user',)
    list_display_links = ('id',)



admin.site.register(User, UserAdmin,)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Notification, NotificationAdmin)
