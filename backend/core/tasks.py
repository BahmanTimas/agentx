from backend.core.models import Conversation
from backend.client import openai, divar
import json


def process_conversation_update(conversation: Conversation):
    prompt = generate_prompt(conversation)
    completion_result = openai.chat_completion(prompt)
    result = completion_result.choices[0].message.content

    divar.send_message(
        conversation.post.divar_access_token.get("access_token"), conversation.divar_conversation_id, result
    )

    prompt = generate_summary_prompt(conversation)
    completion_result = openai.chat_completion(prompt)
    result = completion_result.choices[0].message.content
    conversation.status = result
    conversation.update_at = datetime.datetime.now()
    conversation.save()

    # TODO: do we need tosave our response message too (use divar api) or it will be send to webhook?
    # TODO: do we need to update the post status based on all it's conversation status?


def generate_prompt(conversation: Conversation) -> str:
    previous_messages = conversation.messages

    # Prepare previous conversation messages
    conversation_history = ""
    for message in previous_messages:
        sender = "Supplier" if message["payload"]["sender"]["is_supply"] else "Client"
        text = message["payload"]["data"].get("text", "")
        conversation_history += f"{sender}: {text}\n"

    # Format the prompt
    prompt = f"""
You are a chatbot assistant for a post on Divar.ir.
Respond concisely based on the following post details and previous conversation.

Post Details:
{conversation.post.divar_post_data}
Previous Conversation:
{conversation_history}

Response:
"""
    return prompt.strip()


def generate_summary_prompt(conversation: Conversation) -> str:
    previous_messages = conversation.messages

    # Prepare conversation content for summary
    conversation_content = ""
    for message in previous_messages:
        sender = "Supplier" if message["payload"]["sender"]["is_supply"] else "Client"
        text = message["payload"]["data"].get("text", "")
        conversation_content += f"{sender}: {text}\n"
    
    # Format the summary prompt
    prompt = f"""
You are an assistant summarizing a conversation in a Divar.ir chat. 
Analyze the messages below and generate a summary focusing on key points, inquiries, and responses. 
Highlight any important parts relevant to price, product condition, availability, or other notable information.

Conversation:
{conversation_content}

Summary:
"""
    return prompt.strip()