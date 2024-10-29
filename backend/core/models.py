from django.db import models
import enum


@enum.unique
class Configurations(str, enum.Enum):
    POST_CONVERSATION_RESPOND_PROMPT = "POST_CONVERSATION_RESPOND_PROMPT"
    POST_CONVERSATION_STATUS_PROMPT = "POST_CONVERSATION_STATUS_PROMPT"

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]


class Configuration(models.Model):
    key = models.CharField(max_length=1024, unique=True, choices=Configurations.choices())
    value = models.TextField(null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.key

    @staticmethod
    def get_value(key: str):
        return Configuration.objects.get(key=key).value


class PostDetail(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)
    divar_post_token = models.TextField(null=False, blank=False, unique=True)
    divar_post_return_url = models.TextField(null=False, blank=False)
    divar_post_data = models.JSONField(null=False, blank=False, default=dict)
    divar_access_token = models.JSONField(null=True, blank=True, default=dict)
    divar_on_message_setup = models.BooleanField(null=False, blank=False, default=False)
    knowledge = models.TextField(null=True, blank=True)


class Conversation(models.Model):
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now_add=True)
    divar_conversation_id = models.TextField(null=False, blank=False, unique=True)
    post = models.ForeignKey(PostDetail, on_delete=models.PROTECT, null=False, blank=False)
    messages = models.JSONField(null=False, blank=False, default=list)
    status = models.TextField(null=True, blank=True)


class ChatCompletionHistory(models.Model):  #TODO: change history to detail
    create_at = models.DateTimeField(auto_now_add=True)
    prompt = models.TextField(null=False, blank=False)
    result =  models.TextField(null=False, blank=False)
