import json
import requests
from logger import HaivenLogger
from utils.apih_util import ApihUtil


class KmverseUtil:
    def __init__(self, config_data: dict, apih_util: ApihUtil):
        self.apih_util = apih_util
        self.base_url = config_data.get('base_url')
        self.kmverse_key = config_data.get('kmverse_key')
        self.function_path: dict = config_data.get('function_path')

        self.headers = {
            'km-verse-key': self.kmverse_key,
            'X-API-KEY': self.apih_util.client_id,
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }

        self.retrieval_url = self.base_url + self.function_path["retrieval"]

    def retrieval(self, user_query: str, knowledge_base_id: int, top_k: int = 3, score: int = 35) -> list:
        payload = {
            "projectId": 79,
            "relation": [
                {
                    "knowledgeBaseId": knowledge_base_id,
                    "embedding": ""
                }
            ],
            "query": user_query,
            "indexMode": "hybrid",
            "similarityTopK": top_k,
            "score": score
        }
        self.headers["Authorization"] = "Bearer " + self.apih_util.get_token("CN")

        response = requests.post(
            self.retrieval_url,
            headers=self.headers,
            data=json.dumps(payload),
            verify=False
        )

        result = []

        try:
            resp_json = response.json()
            if resp_json.get("code", 501) != 200:
                HaivenLogger.get().info("KMVerse retrieval error", str(resp_json))
                return result
            one_result = {}
            for each in resp_json["result"]:
                one_result["text"] = each["text"]
                one_result["score"] = each["score"]
                one_result["metadata"] = each["metadata"]
                one_result["doc_id"] = each["docId"]
                metadata = json.loads(each.get("metadata", "{}"))
                one_result["file_name"] = metadata.get("file_name", "")
                result.append(one_result)
            HaivenLogger.get().info(f"KMVerse retrieval success: {len(result)} results found", f"question {json.dumps(user_query)}.")
            return result

        except Exception as e:
            HaivenLogger.get().info(f"KMVerse retrieval exception: {e}", f"response: {json.dumps(response.json())}")
            return result


if __name__ == '__main__':
    kmverse_config = {
        "base_url": "https://apihub-test.lenovo.com/uat/v2/product/tpass",
        "kmverse_key": "/82hgNJsIKB3glxxO6PKnUbC2eIuMLKLLAfGAHpgdjk=",
        "function_path": {
            "retrieval": "/tpass/kmverse/outerapi/v1/knowledge/retrieval"
        }
    }
    apih_config = {
        "auth_url": "https://apihub-test.lenovo.com/token",
        "account": "api_itagent_rq",
        "client_id": "CU7re5hP7RkCs2eUF6ZROg7quBl7QJka",
        "client_secret": "P_U6pzx3a3"
    }
    apih_util = ApihUtil(apih_config)
    kmverse_util = KmverseUtil(kmverse_config, apih_util)

    results = kmverse_util.retrieval("LGVM是什么", 146785204070917)
    print(results)