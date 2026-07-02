import os
import sys
import json
from dotenv import load_dotenv

sys.path.append("/home/farhad/openclaw")
load_dotenv("/home/farhad/openclaw/.env")

from src.config import Config
from src.agent import OpenClawAgent
from src.tools import TOOLS_SCHEMA, execute_tool

config = Config("/home/farhad/openclaw/.env")
agent = OpenClawAgent(config)

prompt = "Search the web for the CVPR 2024 YOLO-World paper, locate its PDF URL on openaccess.thecvf.com, then download it using download_file to /tmp/cvpr_paper.pdf."

from src.persona import SYSTEM_INSTRUCTIONS

# Let's run a manual loop to see exactly what is returned
messages = [
    {"role": "system", "content": SYSTEM_INSTRUCTIONS}
]
messages.append({"role": "user", "content": prompt})

known_tools = {t["function"]["name"] for t in TOOLS_SCHEMA}

print("=== START LOOP ===")
for step in range(1, 6):
    print(f"\n--- STEP {step} ---")
    try:
        response_msg = agent.nim_client.chat_completion(messages, tools=TOOLS_SCHEMA)
        print("Model Response:")
        print(json.dumps(response_msg, indent=2))
        
        tool_calls = response_msg.get("tool_calls")
        if not tool_calls:
            print("No tool calls. Final answer:", response_msg.get("content"))
            break
            
        valid_tool_calls = [tc for tc in tool_calls if tc["function"]["name"] in known_tools]
        if not valid_tool_calls:
            print("No valid tool calls.")
            break
            
        single_tool_call = valid_tool_calls[0]
        func_name = single_tool_call["function"]["name"]
        args = json.loads(single_tool_call["function"]["arguments"])
        
        print(f"Executing tool: {func_name} with args: {args}")
        result = execute_tool(func_name, args)
        print(f"Result (truncated): {result[:300]}")
        
        # Append assistant and tool response
        sanitized_response = {
            "role": "assistant",
            "content": response_msg.get("content") or "",
            "tool_calls": [single_tool_call]
        }
        messages.append(sanitized_response)
        messages.append({
            "role": "tool",
            "tool_call_id": single_tool_call["id"],
            "name": func_name,
            "content": result
        })
    except Exception as e:
        print("Error in step:", e)
        break
