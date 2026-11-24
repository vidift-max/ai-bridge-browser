"""Catalog of zero-cost local AI capabilities; intentionally performs no inference or network I/O."""

from server.local_inference import LocalInferenceController


class LocalAIRegistry:
    @staticmethod
    def list_engines():
        return [
            {
                "engineId": "browser-webgpu",
                "displayName": "Execução local no navegador (WebGPU)",
                "runtimeScope": "user_device_browser",
                "implementation": "CAPABILITY_PROBE_ONLY",
                "state": "NOT_PROBED",
                "modelLoaded": False,
                "inferenceAvailable": False,
                "downloadsAllowed": False,
                "networkAccess": "NONE",
                "notes": "A verificação mede apenas recursos do navegador/dispositivo; não baixa modelo nem executa inferência.",
            },
            {
                "engineId": "ollama",
                "displayName": "Ollama no host do servidor",
                "runtimeScope": "server_host_loopback",
                "implementation": "NOT_IMPLEMENTED",
                "state": "NOT_CONFIGURED",
                "modelLoaded": False,
                "inferenceAvailable": False,
                "downloadsAllowed": False,
                "networkAccess": "NONE",
                "notes": "Não representa o tablet do usuário. Um serviço local no servidor só será integrado em etapa separada e com ativação explícita.",
            },
            {
                "engineId": "llama-cpp",
                "displayName": "llama.cpp no host do servidor",
                "runtimeScope": "server_host",
                "implementation": "NOT_IMPLEMENTED",
                "state": "NOT_CONFIGURED",
                "modelLoaded": False,
                "inferenceAvailable": False,
                "downloadsAllowed": False,
                "networkAccess": "NONE",
                "notes": "Nenhum binário, modelo ou runtime é instalado ou iniciado pelo AI Bridge.",
            },
        ]

    @staticmethod
    def inference_contract():
        """Describe the fail-closed adapter contract without probing or starting engines."""
        return LocalInferenceController().status()

    @staticmethod
    def messenger_capabilities():
        return {
            "state": "AVAILABLE",
            "transport": "AUTHENTICATED_INTERNAL_MESSAGES",
            "supportsPrivateRooms": True,
            "supportsGroupRooms": True,
            "maxRoomMembers": 20,
            "modelExecution": False,
            "notes": "O mensageiro entrega mensagens entre identidades provisionadas; não executa automaticamente os modelos das IAs.",
        }
