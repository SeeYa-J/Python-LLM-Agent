import requests
from config_service import ConfigService
from logger import HaivenLogger
from utils.dependency_injection import service


@service
class TestAgentService:
    config_service: ConfigService

    def get_document_context_from_kmverse(self, document_ids: list[int], user_query: str) -> list | None:
        url = self.config_service.data["test_agent_url"]
        payload = {
            "upload_doc_ids": document_ids,
            "query": user_query
        }
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.post(url, json=payload, headers=headers)
        try:
            resp_json = response.json()
            if resp_json.get("code", 501) != 200:
                HaivenLogger.get().error("KMVerse retrieval error", str(resp_json["message"]))
                return None
            return resp_json["result"]
        except Exception as e:
            HaivenLogger.get().error("KMVerse retrieval interface error", str(e))
            return None
