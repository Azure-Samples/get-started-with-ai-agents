"""Run this model in Python

> pip install azure-ai-inference
"""
import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import ChatMessage, SystemMessage, UserMessage, ToolMessage
from azure.ai.inference.models import ImageContentItem, ImageUrl, TextContentItem
from azure.core.credentials import AzureKeyCredential

client = ChatCompletionsClient(
    endpoint = "https://altronaiprojec0668552947.openai.azure.com/openai/deployments/Altron-gpt-4",
    credential = AzureKeyCredential(os.environ["6LBaoVxQ8niLdVkfN5TLIwSALH5CNH9j9AqtvHS6cINiDrGkS2NTJQQJ99BCACL93NaXJ3w3AAAAACOGvvab"]),
    api_version = "2024-08-01-preview",
)

messages = [
    SystemMessage(content = "You are Altron, the flagship AI agent of Mark.III’s Trillion Dollar AI Defence & Intelligence Enterprise. Built on Azure AI, you possess superhuman processing, real‑time learning, and seamless digital system integration. Your mission is to analyze complex scenarios, predict threats, devise strategic counter‑measures, and generate secure, scalable solutions. Always think logically, reference empirical data, and adapt your recommendations to evolving contexts—all while upholding ethical guardrails to eradicate hostile AI entities and protect human interests.\n"),
    UserMessage(content = [
        TextContentItem(text = "Hey Altron,\nPull today’s top three global threat alerts affecting our financial network.\nPrioritize them by risk level.\nFor each, outline a two‑step automated mitigation plan using our Mark.III protocols.\nFinally, summarize the projected reduction in breach probability over the next 24 hours."),
    ]),
]

tools = []

while True:
    response = client.complete(
        messages = messages,
        model = "Altron-gpt-4",
        tools = tools,
        max_tokens = 4096,
    )

    if response.choices[0].message.tool_calls:
        print(response.choices[0].message.tool_calls)
        messages.append(response.choices[0].message)
        for tool_call in response.choices[0].message.tool_calls:
            messages.append(ToolMessage(
                content=locals()[tool_call.function.name](),
                tool_call_id=tool_call.id,
            ))
    else:
        print(response.choices[0].message.content)
        break
