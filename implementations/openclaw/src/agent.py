import json
import logging
from typing import Dict, Any, List, Optional
from src.config import Config
from src.nim_client import NIMClient
from src.googooli_client import GoogooliClient
from src.persona import SYSTEM_INSTRUCTIONS
from src.tools import TOOLS_SCHEMA, execute_tool

class OpenClawAgent:
    def __init__(self, config: Config):
        self.config = config
        self.nim_client = NIMClient(
            api_key=config.nvidia_api_key,
            base_url=config.nvidia_api_base,
            model_name=config.nvidia_model_name
        )
        self.googooli_client = GoogooliClient(
            api_url=config.googooli_api_url,
            api_key=config.googooli_api_key
        )
        self.history = {}  # user_id -> list of messages

    def handle_message(self, message_text: str, user_id: str = "default") -> str:
        # Handle session reset
        if message_text == "🧹 Reset Session":
            if user_id in self.history:
                self.history[user_id] = []
            return "Session reset successfully."

        # 1. Fetch relevant context from Googooli endpoint if possible
        context = self.googooli_client.query_context(message_text)

        # 2. Prepare chat messages
        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTIONS}
        ]

        if context:
            # Inject context
            messages.append({
                "role": "system",
                "content": f"Relevant context from Googooli system:\n{context}"
            })

        # Append historical messages for this user (limit to last 15 messages)
        user_history = self.history.get(user_id, [])
        messages.extend(user_history[-15:])

        # Append current user message
        messages.append({"role": "user", "content": message_text})

        # Keep track of messages added during this turn
        new_messages = [{"role": "user", "content": message_text}]

        # 3. Agent Execution Loop (up to 5 steps of tool executions)
        known_tools = {t["function"]["name"] for t in TOOLS_SCHEMA}
        final_reply = ""
        for _ in range(5):
            response_msg = self.nim_client.chat_completion(messages, tools=TOOLS_SCHEMA)
            
            tool_calls = response_msg.get("tool_calls")
            if not tool_calls:
                final_reply = response_msg.get("content") or ""
                break

            valid_tool_calls = [tc for tc in tool_calls if tc["function"]["name"] in known_tools]
            if not valid_tool_calls:
                final_reply = response_msg.get("content") or "Error: The model generated an invalid tool call."
                break

            # Nvidia NIM model template only supports a single tool call per turn
            single_tool_call = valid_tool_calls[0]

            # Construct sanitized assistant response message (only standard fields)
            sanitized_response = {
                "role": "assistant",
                "content": response_msg.get("content") or "",
                "tool_calls": [single_tool_call]
            }
            messages.append(sanitized_response)
            new_messages.append(sanitized_response)

            func_name = single_tool_call["function"]["name"]
            try:
                args = json.loads(single_tool_call["function"]["arguments"])
            except Exception:
                args = {}
            
            logging.info(f"Executing tool {func_name} with args {args}")
            result = execute_tool(func_name, args)
            
            tool_response = {
                "role": "tool",
                "tool_call_id": single_tool_call["id"],
                "name": func_name,
                "content": result
            }
            messages.append(tool_response)
            new_messages.append(tool_response)
        else:
            final_reply = "Error: Maximum tool execution depth reached."

        # Save final assistant reply to history
        new_messages.append({"role": "assistant", "content": final_reply})
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].extend(new_messages)

        return final_reply
