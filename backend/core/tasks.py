from backend.core.models import Conversation
from backend.client import openai, divar


async def process_conversation_update(conversation: Conversation):
    prompt = generate_prompt(conversation)
    completion_result = openai.chat_completion(prompt)
    result = json.loads(completion_result.choices[0].message.content)

    divar.send_message(
        conversation.post.divar_access_token.get("access_token"), conversation.divar_conversation_id, result
    )

    prompt = generate_summary_prompt(conversation)
    completion_result = openai.chat_completion(prompt)
    result = json.loads(completion_result.choices[0].message.content)
    conversation.status = result
    conversation.update_at = datetime.datetime.now()
    conversation.save()

    # TODO: do we need tosave our response message too (use divar api) or it will be send to webhook?
    # TODO: do we need to update the post status based on all it's conversation status?


def generate_prompt(conversation: Conversation) -> str:
    post_info = conversation.post.divar_post_data
    previous_messages = conversation.messages

    # Extract key data from post_info
    brand_model = post_info['data'].get('brand_model', 'Unknown model')
    color = post_info['data'].get('color', 'Unknown color')
    description = post_info['data'].get('description', 'No description available')
    price = post_info['data']['price'].get('value', 'Unknown price')
    price_mode = post_info['data']['price'].get('mode', 'Not specified')
    status = post_info['data'].get('status', 'Unknown condition')
    location = f"{post_info.get('city', 'Unknown city')} - {post_info.get('district', 'Unknown district')}"
    
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
- Category: {post_info.get('category', 'Unknown category')}
- Brand/Model: {brand_model}
- Color: {color}
- Condition: {status}
- Price: {price} ({price_mode})
- Location: {location}
- Description: {description}
- Other Details: {} #TODO: knowdelge here
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