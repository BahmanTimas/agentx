from django.contrib import admin
from backend.core.models import PostDetail, Conversation, Configuration

admin.site.register(PostDetail)
admin.site.register(Conversation)
admin.site.register(Configuration)