import time
import requests

class ApihUtil:
    auth_url: str
    account: str
    client_id: str
    client_secret: str
    tokenMap = {}

    def __init__(self, config_data: dict):
        self.auth_url = config_data.get("auth_url")
        self.account = config_data.get("account")
        self.client_id = config_data.get("client_id")
        self.client_secret = config_data.get("client_secret")

    def get_new_token(self, region):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "X-API-KEY": self.client_id
        }
        request_data = {
            "username": self.account,
            "password": self.client_secret,
        }
        response = requests.post(url=self.auth_url, data=request_data, headers=headers, verify=False)
        response = response.json()
        if response.get('access_token'):
            self.tokenMap[region] = {
                'accessToken': response.get('access_token'),
                'expiresAt': time.time() + response.get('expires_in') - 30  # 提前30S拿token
            }
            return response.get('access_token')
        else:
            return "error: " + str(response)

    def get_token(self, region):
        if region not in self.tokenMap or self.tokenMap[region]['expiresAt'] < time.time():
            return self.get_new_token(region)
        return self.tokenMap[region]['accessToken']