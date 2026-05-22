import os
import json
import re
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from rag_engine import search
from agent import TOOLS, execute_tool

app = Flask(__name__)

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-latest")

# Conversation history (in memory for demo)
conversation_history = []

def build_system_prompt(rag_results):
    """Build the system prompt with RAG context and tool definitions"""
    rag_context = ""
    for i, doc in enumerate(rag_results):
        rag_context += f"\n--- Document {i+1} (from {doc['source']}) ---\n{doc['content']}\n"

    tools_description = ""
    for tool in TOOLS:
        tools_description += f"\n- {tool['name']}: {tool['description']}"
        tools_description += f"\n  Parameters: {tool['parameters']}\n"

    system_prompt = f"""You are an intelligent IT Helpdesk Support Agent for a software company.

YOUR KNOWLEDGE BASE (retrieved from IT documentation):
{rag_context}

YOUR AVAILABLE TOOLS:
{tools_description}

INSTRUCTIONS:
1. Use the knowledge base above to answer the user's IT issue clearly and step by step.
2. If the user's issue needs a support ticket to be created, use the create_ticket tool.
3. If the user provides a ticket ID and wants to check status, use check_ticket_status tool.
4. If an issue is critical (P1/P2) or user requests escalation, use escalate_ticket tool.
5. Always be professional, clear, and helpful.
6. When you decide to use a tool, respond ONLY with this exact JSON format and nothing else:
   {{"tool_call": true, "tool_name": "tool_name_here", "parameters": {{"param1": "value1"}}}}
7. After a tool is executed, you will receive the result and should then respond naturally to the user.
8. If you don't need to use a tool, just respond normally in plain text.
"""
    return system_prompt

def chat_with_gemini(user_message, rag_results):
    """Send message to Gemini with context and conversation history"""
    global conversation_history

    system_prompt = build_system_prompt(rag_results)

    # Build full conversation for Gemini
    messages = []

    # Add conversation history
    for msg in conversation_history[-6:]:  # keep last 6 messages as context
        messages.append(msg)

    # Add current user message
    messages.append({"role": "user", "parts": [user_message]})

    # Prepend system prompt to first user message
    if messages:
        messages[0]["parts"][0] = system_prompt + "\n\nUser: " + messages[0]["parts"][0]

    # Call Gemini
    response = model.generate_content(messages)
    response_text = response.text.strip()

    # Check if Gemini wants to use a tool
    tool_result = None
    tool_used = None
    final_response = response_text

    # Try to parse tool call from response
    try:
        # Look for JSON tool call in response
        json_match = re.search(r'\{.*"tool_call".*\}', response_text, re.DOTALL)
        if json_match:
            tool_call = json.loads(json_match.group())
            if tool_call.get("tool_call") == True:
                tool_name = tool_call["tool_name"]
                parameters = tool_call["parameters"]
                tool_used = tool_name

                # Execute the tool
                tool_result = execute_tool(tool_name, parameters)

                # Send tool result back to Gemini for natural response
                follow_up = f"Tool '{tool_name}' was executed. Result: {json.dumps(tool_result)}. Now respond naturally to the user about what was done."
                follow_up_messages = messages + [
                    {"role": "model", "parts": [response_text]},
                    {"role": "user", "parts": [follow_up]}
                ]
                follow_up_response = model.generate_content(follow_up_messages)
                final_response = follow_up_response.text.strip()
    except Exception as e:
        print(f"Tool parsing error: {e}")

    # Update conversation history
    conversation_history.append({"role": "user", "parts": [user_message]})
    conversation_history.append({"role": "model", "parts": [final_response]})

    return {
        "response": final_response,
        "tool_used": tool_used,
        "tool_result": tool_result
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY not set"}), 500

    # Step 1: RAG - search for relevant documents
    rag_results = search(user_message, top_k=2)

    # Step 2: Chat with Gemini using context + agent tools
    result = chat_with_gemini(user_message, rag_results)

    return jsonify({
        "response": result["response"],
        "rag_results": rag_results,
        "tool_used": result["tool_used"],
        "tool_result": result["tool_result"],
        "context_length": len(conversation_history)
    })

@app.route('/reset', methods=['POST'])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "Conversation reset"})

if __name__ == '__main__':
    print("Starting IT Helpdesk Agent...")
    print("Make sure GEMINI_API_KEY is set as environment variable")
    app.run(debug=True, port=5000)
