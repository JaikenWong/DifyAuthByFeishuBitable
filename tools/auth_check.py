from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage


def _get_tenant_access_token(app_id: str, app_secret: str) -> str:
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(
            f"Failed to get access token: {data.get('msg', 'unknown error')} (code={data.get('code')})"
        )
    return data["tenant_access_token"]


def _extract_field_text(value: Any) -> str:
    """Normalize Bitable field value to plain string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(item.get("text") or item.get("name") or str(item))
            else:
                parts.append(str(item))
        return ",".join(parts)
    if isinstance(value, dict):
        return value.get("text") or value.get("name") or str(value)
    return str(value)


class AuthCheckTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage, None, None]:
        app_id = tool_parameters["app_id"]
        app_secret = tool_parameters["app_secret"]

        app_token = tool_parameters["app_token"]
        table_id = tool_parameters["table_id"]
        view_id = tool_parameters.get("view_id") or ""
        employee_col = tool_parameters["employee_col"]
        permission_col = tool_parameters.get("permission_col") or ""
        user_id = tool_parameters["user_id"]

        try:
            access_token = _get_tenant_access_token(app_id, app_secret)
        except (RuntimeError, requests.RequestException) as e:
            yield self.create_text_message(f"no")
            yield self.create_json_message({
                "result": "no",
                "permission_value": "",
                "message": f"Auth service error: {e}",
            })
            return

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        search_body: dict[str, Any] = {
            "filter": {
                "conjunction": "and",
                "conditions": [
                    {
                        "field_name": employee_col,
                        "operator": "is",
                        "value": [user_id],
                    }
                ],
            },
            "page_size": 2,
        }
        if view_id:
            search_body["view_id"] = view_id

        try:
            resp = requests.post(
                f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/search",
                headers=headers,
                json=search_body,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            yield self.create_text_message(f"no")
            yield self.create_json_message({
                "result": "no",
                "permission_value": "",
                "message": f"Bitable query failed: {e}",
            })
            return

        if data.get("code") != 0:
            yield self.create_text_message(f"no")
            yield self.create_json_message({
                "result": "no",
                "permission_value": "",
                "message": f"Bitable error: {data.get('msg', 'unknown error')} (code={data.get('code')})",
            })
            return

        items = data.get("data", {}).get("items", [])

        if not items:
            yield self.create_text_message(f"no")
            yield self.create_json_message({
                "result": "no",
                "permission_value": "",
                "message": "Unauthorized",
            })
            return

        if len(items) > 1:
            yield self.create_text_message(f"no")
            yield self.create_json_message({
                "result": "no",
                "permission_value": "",
                "message": f"Duplicate user records found for '{user_id}', contact admin.",
            })
            return

        fields = items[0].get("fields", {})

        permission_value = ""
        if permission_col:
            if permission_col in fields:
                permission_value = _extract_field_text(fields[permission_col])

        yield self.create_text_message(f"yes")
        yield self.create_json_message({
            "result": "yes",
            "permission_value": permission_value,
            "message": "Authorization passed",
        })
