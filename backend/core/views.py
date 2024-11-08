from django.shortcuts import render, redirect
import json
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from rest_framework.response import Response
from django.shortcuts import render
from backend.client import divar
from backend.core.models import PostDetail, Conversation
import asyncio
from backend.core.tasks import process_conversation_update
import logging


@api_view(["GET", "POST"])
def landing(request):
    return render(request, 'landing.html')


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
            divar_post_token=divar_post_token
        )
        post_detail.divar_post_return_url=divar_post_return_url
        post_detail.divar_post_data = divar_post_data
        post_detail.knowledge=knowledge
        post_detail.save()

        if not post_detail.divar_access_token:  # TODO: check for expire too
            oauth_grant_url = divar.create_oauth_init_url(
                post_token=divar_post_token,
                scope=f'CHAT_POST_CONVERSATIONS_READ.{divar_post_token}+CHAT_POST_CONVERSATIONS_MESSAGE_SEND.{divar_post_token}'
            )
            return redirect(oauth_grant_url)
        else: return render(request, 'appstart.html', context=get_appstart_context(post_detail))

    # TODO: check params?
    # return_url = request.GET.get("return_url")

    divar_post_token = request.GET.get("post_token")
    post_detail = PostDetail.objects.filter(divar_post_token=divar_post_token).first()

    return render(request, 'appstart.html', context=get_appstart_context(post_detail))


def get_appstart_context(post_detail: PostDetail):
    if post_detail:
        conversations = post_detail.conversation_set.all()
        conversations_summary = [{
            'id': conversation.id,
            'status': conversation.status,
        } for conversation in conversations]

        return {
            'activated': bool(post_detail) and bool(post_detail.divar_access_token) and bool(post_detail.divar_on_message_setup),
            'knowledge': post_detail.knowledge,
            'private_knowledge': True,
            'tone': 'frieldly',
            'conversations': conversations_summary,
            'post_status': post_detail.status,
            'answers_count': 32 # we need to store this data each time we use divar send_message
        }

    return { 'activated': False }

@api_view(["POST"]) #nemikhaim?
# @authentication_classes([JWTStatelessUserAuthentication])
# @permission_classes([IsAuthenticated])
def chat_start(request):
    user_id = request.user.id

    # chi bebine? bere OAuth2? ke beshe chat kone?

    #logging.info(request.POST)  #{"callback_url":"https://open-platform-redirect.divar.ir/completion","post_token":"post-token","user_id":"demand_id","peer_id":"supplier_id","supplier":{"id":"supplier_id"},"demand":{"id":"demand_id"}}
    
    return HttpResponse("https://agentx.darkube.app/app_start?source=chat_start")


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

    logging.info("Response Headers:", request.headers)

    data = json.loads(request.body.decode('utf-8'))

    logging.info(f"receive on message payload: {data}")
    
    divar_post_token = data.get("payload").get("metadata").get("post_token")
    
    post_detail = PostDetail.objects.get(divar_post_token=divar_post_token)
    
    conversation, created = Conversation.objects.get_or_create(
        post=post_detail,
        divar_conversation_id=data.get("payload").get("conversation_id")
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

    sender = data.get("payload").get("sender")

    if not sender.get("is_supply"):
        # TODO: mark conversation to not respond automatically anymore (age taraf ba moshtari sohbat kone dg bot javab nade be payame moshtari)
        process_conversation_update(conversation)

    return Response(status=200)


@api_view(["GET"])
def oauth_callback(request):
    if request.GET.get("error"): # TODO
        logging.info(request.GET.get("error"))
        logging.info(request.GET.get("error_description"))
        return render(request, 'error.html', context={"oautherror": True, "return_url": "https://divar.ir/my-divar/my-posts", "error_description": request.GET.get("error_description")})

    # scope = request.GET.get("scope")
    state = request.GET.get("state")
    divar_post_token = state.split("_")[0]

    code = request.GET.get("code")
    divar_access_token = divar.get_access_token(code)

    # get access token save it in the post and return to post return url
    post_detail = PostDetail.objects.filter(divar_post_token=divar_post_token).first()
    post_detail.divar_access_token = divar_access_token
    post_detail.save()

    # TODO: do we need a middle page that notify the user we are processing the data needed?

    # TODO: response? save the response? error handling
    if not post_detail.divar_on_message_setup:
        divar.setup_post_on_message_hook(divar_post_token, divar_access_token.get("access_token"))
        post_detail.divar_on_message_setup = True
        post_detail.save()

    return redirect(post_detail.divar_post_return_url)
