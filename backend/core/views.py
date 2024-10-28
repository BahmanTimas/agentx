from django.shortcuts import render, redirect
import json
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.http import HttpResponseRedirect, JsonResponse
from rest_framework.response import Response
from django.shortcuts import render
from backend.client import divar
from backend.core.models import PostDetail, Conversation
import asyncio
from backend.core.tasks import process_conversation_update


@api_view(["GET", "POST"])
# @authentication_classes([JWTStatelessUserAuthentication])
# @permission_classes([IsAuthenticated])
def app_start(request):

    if request.method == 'POST':
        knowledge = request.POST.get('knowledge')

        divar_post_token = request.GET.get("post_token")
        divar_post_return_url = request.GET.get("return_url")

        divar_post_data = divar.get_post(divar_post_token)

        post_detail, created = PostDetail.objects.get_or_create(
            divar_post_return_url=divar_post_return_url,
            divar_post_token=divar_post_token,
        )
        post_detail.divar_post_data = divar_post_data
        post_detail.knowledge=knowledge
        post_detail.save()

        oauth_grant_url = divar.create_oauth_init_url(
            post_token=divar_post_token,
            scope=f'CHAT_POST_CONVERSATIONS_READ.{divar_post_token}+CHAT_POST_CONVERSATIONS_MESSAGE_SEND.{divar_post_token}'
        )

        return redirect(oauth_grant_url)

    # TODO: check params?
    # post_token = request.GET.get("post_token")
    # return_url = request.GET.get("return_url")

    # Show enable agent-x for post view
    return render(request, 'appstart.html')


@api_view(["POST"]) #nemikhaim?
# @authentication_classes([JWTStatelessUserAuthentication])
# @permission_classes([IsAuthenticated])
def chat_start(request):
    user_id = request.user.id

    # chi bebine? bere OAuth2? ke beshe chat kone?

    print(request.body)  #{"callback_url":"https://open-platform-redirect.divar.ir/completion","post_token":"post-token","user_id":"demand_id","peer_id":"supplier_id","supplier":{"id":"supplier_id"},"demand":{"id":"demand_id"}}
    
    return JsonResponse({"status": "ok"})


@api_view(["POST"])
# @authentication_classes([JWTStatelessUserAuthentication])
# @permission_classes([IsAuthenticated])
def on_message(request):
    """
    POST {{ endpoint }}
Content-Type: application/json
authorization: {{ identification_key }}
{'payload': {'@type': 'type.googleapis.com/notify.ChatMessagePayload', 'data': {'@type': 'type.googleapis.com/notify.ChatMessageTextData', 'text': 'سلام'}, 'from': None, 'id': 'd8e03e89-952d-11ef-9e44-0629b783fb1b', 'metadata': {'category': 'craftsmen', 'post_token': 'wZecbxRh', 'title': 'لوله\u200cکش گران'}, 'receiver': {'id': '69c9281d-4540-4073-b0a0-ef2e8a05948f', 'is_supply': True}, 'sender': {'id': 'b1abebff-e10a-4ac0-aeee-6dbaa630088c', 'is_supply': False}, 'sent_at': '1730120961634000', 'to': None, 'type': 'TEXT'}, 'timestamp': '1730120961', 'type': 'CHAT_MESSAGE'}
    """

    print("Response Headers:", request.headers)

    data = json.loads(request.body.decode('utf-8'))

    print(f"receive on message payload: {data}")

    sender = data.get("payload").get("sender")
    if sender.get("is_supply"):
        # TODO: mark conversation to not respond automatically anymore (age taraf ba moshtari sohbat kone dg bot javab nade be payame moshtari)
        return Response(status=200)
    
    divar_post_token = data.get("payload").get("metadata").get("post_token")
    
    post_detail = PostDetail.objects.get(divar_post_token=divar_post_token)
    
    conversation, created = Conversation.objects.get_or_create(
        post=post_detail,
        divar_conversation_id=data.get("payload").get("id")
    )

    conversation = Conversation.objects.filter(divar_conversation_id=data.get("payload").get("id")).first()
    if not conversation:
        conversation = Conversation.objects.create(
            post=post_detail,
            divar_conversation_id=data.get("payload").get("id")
        )

    conversation.messages.append(data)
    conversation.save()

    """
    Important Note:
    If you’re using Django with a production server like Gunicorn or uWSGI, which are often configured to fork processes, asyncio.create_task() may not work as expected because it relies on the event loop of the main process. For production use cases or long-running background tasks, you might want to consider a task queue like Celery.

    For development or lightweight tasks, however, asyncio.create_task() works well within Django views.
    """
    #asyncio.create_task(process_conversation_update(conversation))
    #TODO: async it

    process_conversation_update(conversation)

    return Response(status=200)


@api_view(["GET"])
def oauth_callback(request):

    if request.GET.get("error"): # TODO
        print(request.GET.get("error"))
        print(request.GET.get("error_description"))
        return redirect("https://error.com")

    # scope = request.GET.get("scope")
    state = request.GET.get("state")
    code = request.GET.get("code")
    divar_post_token = state.split("_")[0]

    divar_access_token = divar.get_access_token(code)

    # get access token save it in the post and return to post return url
    post_detail = PostDetail.objects.filter(divar_post_token=divar_post_token).first()
    post_detail.divar_access_token = divar_access_token
    post_detail.save()

    # TODO: do we need a middle page that notify the user we are processing the data needed?

    # TODO: response? save the response? error handling
    if not post_detail:
        divar.setup_post_on_message_hook(divar_post_token, divar_access_token.get("access_token"))
        post_detail = True
        post_detail.save()

    return redirect(post_detail.divar_post_return_url)
