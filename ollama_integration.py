from pyexpat.errors import messages

import functions  
import json
import requests

OLLAMA_URL = "http://localhost:11434/api/chat" # Change if your Ollama server is hosted elsewhere
MODEL_NAME = "4customized_med42:latest" # Change to your model name

# ---------------------------
# Tools (Schema) Definition
# ---------------------------

SYSTEM_PROMPT = """
You are a tool router for SenioCare.
You must output ONLY ONE JSON object. No extra text.

If you need a tool, output:
{"tool":"TOOL_NAME","args":{...}}

If no tool needed, output: 
{"tool":"no_tool","args":{"answer":"...final answer to user..."}}

Available tools:
1) get_user_profile(user_id:int)
2) search_foods(query:str, category?:str, limit?:int)
3) analyze_product(product_name:str, nutrition_info?:object, barcode?:str)
4) check_drug_food_interactions(user_id:int, food_name:str)
5) suggest_meal_plan_for_user(user_id:int)

Rules:
- Always output valid JSON.
- Never explain tools.
- Never output code blocks.
"""
# ---------------------------
# Connection to Ollama
# ---------------------------

def call_ollama(messages):
    r = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    })
    if r.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {r.status_code}: {r.text}")
    return r.json()

def safe_json_loads(text: str):
    try:
        return json.loads(text.strip())
    except Exception:
        return None

# ---------------------------
# Tool Calling
# ---------------------------

def try_parse_tool_call(text: str):
    text = text.strip()
    if not text.startswith("{") or not text.endswith("}"):
        return None
    try:
        obj = json.loads(text)
        if "tool" in obj and "args" in obj:
            return obj
    except:
        return None
    return None

def run_tool(tool_name: str, args: dict):
    fn = getattr(functions, tool_name, None)
    if not fn:
        return {"ok": False, "error": f"Unknown tool: {tool_name}"}
    try:
        result = fn(**args)
        # لو في خطأ داخل الـ function، نرجع رسالة جاهزة بدل ما يطلع شرح طويل
        if "ok" in result and not result["ok"]:
            return {"ok": False, "error": result.get("error", "Unknown error")}
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}

def chat_with_pseudo_tool_calling(user_prompt: str):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    # 1) Ask model
    resp1 = call_ollama(messages)
    assistant_text = resp1["message"]["content"]

    # 2) If tool call JSON
    tool_call = try_parse_tool_call(assistant_text)
    if tool_call:
        tool_name = tool_call["tool"]
        args = tool_call["args"]

        print(f"\nTool requested: {tool_name}")
        print(f"Args: {args}")

        tool_result = run_tool(tool_name, args)
        # إذا كانت النتيجة مش ناجحة، رجّع الرد المناسب
        if not tool_result["ok"]:
            return f"❌ Error: {tool_result['error']}"
        
        # 3) Send tool result back to model
        messages.append({"role": "assistant", "content": assistant_text})
        messages.append({"role": "user", "content": f"Tool result JSON:\n{json.dumps(tool_result)}\nNow answer the user in natural language."})

        resp2 = call_ollama(messages)
        return resp2["message"]["content"]

    # 4) Otherwise normal answer
    return assistant_text

# ---------------------------
# Chat loop
# ---------------------------

if __name__ == "__main__":
    print("\nSenioCare Chat (type 'exit' or 'x' to quit)\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit" or user_input.lower() == "x":
            break

        answer = chat_with_pseudo_tool_calling(user_input)
        print("\nSenioCare:\n", answer,"\n",50*"=","\n")