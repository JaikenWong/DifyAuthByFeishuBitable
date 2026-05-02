import requests
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class FeishuAuthProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict) -> None:
        try:
            resp = requests.post(
                "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": credentials["app_id"],
                    "app_secret": credentials["app_secret"],
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            raise ToolProviderCredentialValidationError(f"Request failed: {e}")

        if data.get("code") != 0:
            raise ToolProviderCredentialValidationError(
                f"Invalid credentials: {data.get('msg', 'unknown error')} (code={data.get('code')})"
            )
