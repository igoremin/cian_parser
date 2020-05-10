from django.contrib import admin
from .models import MapParserDetails, ObjectInfoDetails, ProxyFile, ResultFile, Status

admin.site.register(MapParserDetails)
admin.site.register(ObjectInfoDetails)
admin.site.register(ProxyFile)
admin.site.register(ResultFile)
admin.site.register(Status)
