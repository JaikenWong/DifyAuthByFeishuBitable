from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class FeishuAuthProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict) -> None:
        pass
