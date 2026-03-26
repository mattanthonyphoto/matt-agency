#!/usr/bin/env python3
"""ManyChat MCP Server — manage subscribers, flows, tags, fields, and messaging.

Requires MANYCHAT_API_TOKEN in environment.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

# MCP protocol over stdio
API_BASE = "https://api.manychat.com/fb"
TOKEN = os.environ.get("MANYCHAT_API_TOKEN", "")

def api_call(method, endpoint, data=None, retries=3):
    """Make a ManyChat API call with retry on rate limit."""
    url = f"{API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    for attempt in range(retries):
        try:
            if data is not None:
                req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
            else:
                req = urllib.request.Request(url, headers=headers, method="GET")

            with urllib.request.urlopen(req) as resp:
                body = json.loads(resp.read().decode())
                return body
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            error_body = e.read().decode() if e.fp else str(e)
            return {"status": "error", "message": f"HTTP {e.code}: {error_body}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "Max retries exceeded"}


# ═══════ TOOL DEFINITIONS ═══════

TOOLS = [
    {
        "name": "manychat_page_info",
        "description": "Get ManyChat account info (page name, pro status, timezone)",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "manychat_list_flows",
        "description": "List all automation flows with IDs and names",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "manychat_list_custom_fields",
        "description": "List all custom fields",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "manychat_create_custom_field",
        "description": "Create a custom field",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Field name"},
                "type": {"type": "string", "enum": ["text", "number", "date", "datetime", "boolean"], "description": "Field type"}
            },
            "required": ["name", "type"]
        }
    },
    {
        "name": "manychat_list_tags",
        "description": "List all tags",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "manychat_create_tag",
        "description": "Create a new tag",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Tag name"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "manychat_find_subscriber",
        "description": "Find a subscriber by name",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Subscriber name to search for"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "manychat_get_subscriber",
        "description": "Get subscriber info by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_id": {"type": "string", "description": "Subscriber ID"}
            },
            "required": ["subscriber_id"]
        }
    },
    {
        "name": "manychat_tag_subscriber",
        "description": "Add a tag to a subscriber",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_id": {"type": "string", "description": "Subscriber ID"},
                "tag_id": {"type": "integer", "description": "Tag ID"}
            },
            "required": ["subscriber_id", "tag_id"]
        }
    },
    {
        "name": "manychat_untag_subscriber",
        "description": "Remove a tag from a subscriber",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_id": {"type": "string", "description": "Subscriber ID"},
                "tag_id": {"type": "integer", "description": "Tag ID"}
            },
            "required": ["subscriber_id", "tag_id"]
        }
    },
    {
        "name": "manychat_set_custom_field",
        "description": "Set a custom field value for a subscriber",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_id": {"type": "string", "description": "Subscriber ID"},
                "field_id": {"type": "integer", "description": "Custom field ID"},
                "field_value": {"type": "string", "description": "Value to set"}
            },
            "required": ["subscriber_id", "field_id", "field_value"]
        }
    },
    {
        "name": "manychat_send_flow",
        "description": "Send/trigger a flow for a subscriber",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_id": {"type": "string", "description": "Subscriber ID"},
                "flow_ns": {"type": "string", "description": "Flow namespace ID"}
            },
            "required": ["subscriber_id", "flow_ns"]
        }
    },
    {
        "name": "manychat_send_content",
        "description": "Send content (text message) to a subscriber via Instagram",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subscriber_id": {"type": "string", "description": "Subscriber ID"},
                "text": {"type": "string", "description": "Message text to send"}
            },
            "required": ["subscriber_id", "text"]
        }
    },
    {
        "name": "manychat_list_subscribers",
        "description": "List subscribers with optional tag filter",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tag_id": {"type": "integer", "description": "Filter by tag ID (optional)"},
                "limit": {"type": "integer", "description": "Max results (default 25)"}
            },
            "required": []
        }
    },
    {
        "name": "manychat_list_growth_tools",
        "description": "List growth tools (triggers, widgets, comment triggers)",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    }
]


# ═══════ TOOL EXECUTION ═══════

def execute_tool(name, args):
    """Execute a ManyChat tool and return the result."""
    if name == "manychat_page_info":
        return api_call("GET", "page/getInfo")

    elif name == "manychat_list_flows":
        return api_call("GET", "page/getFlows")

    elif name == "manychat_list_custom_fields":
        return api_call("GET", "page/getCustomFields")

    elif name == "manychat_create_custom_field":
        return api_call("POST", "page/createCustomField", {
            "caption": args["name"],
            "type": args["type"]
        })

    elif name == "manychat_list_tags":
        return api_call("GET", "page/getTags")

    elif name == "manychat_create_tag":
        return api_call("POST", "page/createTag", {"name": args["name"]})

    elif name == "manychat_find_subscriber":
        return api_call("GET", f"subscriber/findByName?name={urllib.parse.quote(args['name'])}")

    elif name == "manychat_get_subscriber":
        return api_call("GET", f"subscriber/getInfo?subscriber_id={args['subscriber_id']}")

    elif name == "manychat_tag_subscriber":
        return api_call("POST", "subscriber/addTag", {
            "subscriber_id": args["subscriber_id"],
            "tag_id": args["tag_id"]
        })

    elif name == "manychat_untag_subscriber":
        return api_call("POST", "subscriber/removeTag", {
            "subscriber_id": args["subscriber_id"],
            "tag_id": args["tag_id"]
        })

    elif name == "manychat_set_custom_field":
        return api_call("POST", "subscriber/setCustomField", {
            "subscriber_id": args["subscriber_id"],
            "field_id": args["field_id"],
            "field_value": args["field_value"]
        })

    elif name == "manychat_send_flow":
        return api_call("POST", "sending/sendFlow", {
            "subscriber_id": args["subscriber_id"],
            "flow_ns": args["flow_ns"]
        })

    elif name == "manychat_send_content":
        return api_call("POST", "sending/sendContent", {
            "subscriber_id": args["subscriber_id"],
            "data": {
                "version": "v2",
                "content": {
                    "type": "instagram",
                    "messages": [
                        {"type": "text", "text": args["text"]}
                    ]
                }
            },
            "message_tag": "CONFIRMED_EVENT_UPDATE"
        })

    elif name == "manychat_list_subscribers":
        params = []
        if args.get("tag_id"):
            params.append(f"tag_id={args['tag_id']}")
        limit = args.get("limit", 25)
        params.append(f"limit={limit}")
        query = "&".join(params)
        return api_call("GET", f"subscriber/getSubscribers?{query}")

    elif name == "manychat_list_growth_tools":
        return api_call("GET", "page/getGrowthTools")

    else:
        return {"status": "error", "message": f"Unknown tool: {name}"}


# ═══════ MCP PROTOCOL (JSON-RPC over stdio) ═══════

def send_response(id, result):
    """Send a JSON-RPC response."""
    msg = {"jsonrpc": "2.0", "id": id, "result": result}
    out = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(out.encode())}\r\n\r\n{out}")
    sys.stdout.flush()

def send_error(id, code, message):
    """Send a JSON-RPC error."""
    msg = {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}
    out = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(out.encode())}\r\n\r\n{out}")
    sys.stdout.flush()

def handle_request(req):
    """Handle a single JSON-RPC request."""
    method = req.get("method", "")
    id = req.get("id")
    params = req.get("params", {})

    if method == "initialize":
        send_response(id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "manychat-mcp", "version": "1.0.0"}
        })

    elif method == "notifications/initialized":
        pass  # No response needed for notifications

    elif method == "tools/list":
        send_response(id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        result = execute_tool(tool_name, tool_args)
        send_response(id, {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        })

    elif method == "ping":
        send_response(id, {})

    else:
        if id is not None:
            send_error(id, -32601, f"Method not found: {method}")


def main():
    """Run the MCP server over stdio."""
    import urllib.parse

    if not TOKEN:
        sys.stderr.write("ERROR: MANYCHAT_API_TOKEN environment variable required\n")
        sys.exit(1)

    sys.stderr.write("ManyChat MCP server started\n")

    buf = b""
    while True:
        try:
            chunk = sys.stdin.buffer.read(1)
            if not chunk:
                break
            buf += chunk

            # Parse Content-Length header
            if b"\r\n\r\n" in buf:
                header, rest = buf.split(b"\r\n\r\n", 1)
                header_str = header.decode()
                content_length = 0
                for line in header_str.split("\r\n"):
                    if line.lower().startswith("content-length:"):
                        content_length = int(line.split(":")[1].strip())

                # Read remaining body if needed
                while len(rest) < content_length:
                    more = sys.stdin.buffer.read(content_length - len(rest))
                    if not more:
                        break
                    rest += more

                body = rest[:content_length].decode()
                buf = rest[content_length:]

                try:
                    req = json.loads(body)
                    handle_request(req)
                except json.JSONDecodeError:
                    sys.stderr.write(f"Invalid JSON: {body[:200]}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")


if __name__ == "__main__":
    main()
