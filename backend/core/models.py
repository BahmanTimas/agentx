from django.db import models


class PostDetail(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)
    divar_post_token = models.TextField(null=False, blank=False, unique=True)
    divar_post_return_url = models.TextField(null=False, blank=False, unique=True)
    divar_post_data = models.JSONField(null=False, blank=False, default=dict)
    divar_access_token = models.JSONField(null=True, blank=True, default=dict)
    divar_on_message_setup = models.BooleanField(null=False, blank=False, default=False)
    knowledge = models.TextField(null=True, blank=True)


class Conversation(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)
    divar_conversation_id = models.TextField(null=False, blank=False, unique=True)
    post = models.ForeignKey(PostDetail, on_delete=models.PROTECT, null=False, blank=False)
    user_id = models.TextField(null=False, blank=False)
    messages = models.JSONField(null=False, blank=False, default=list)
    status = models.TextField(null=True, blank=True)
