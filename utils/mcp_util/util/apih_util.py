import time
import requests

config = {
            "auth_url": "https://apihub-test.lenovo.com/token",
            "account": "api_pocm_ai",
            "client_id": "tK1ztB8NJRhDaX3xL49KAs00lTTND3EO",
            "client_secret": "H=c3p4wD=L"
        }

# @DeprecationWarning("请使用utils文件夹下的apih_util.py")
class ApihUtil:
    tokenMap = {}

    @staticmethod
    def get_new_token(region):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "X-API-KEY": config['client_id']
        }
        request_data = {
            "username": config['account'],
            "password": config['client_secret'],
        }
        response = requests.post(url=config['auth_url'], data=request_data, headers=headers, verify=False)
        response = response.json()
        if response.get('access_token'):
            ApihUtil.tokenMap[region] = {
                'accessToken': response.get('access_token'),
                'expiresAt': time.time() + response.get('expires_in') - 30  # 提前30S拿token
            }
            return response.get('access_token')
        else:
            return "error"

    @staticmethod
    def get_token(region):
        if region not in ApihUtil.tokenMap or ApihUtil.tokenMap[region]['expiresAt'] < time.time():
            return ApihUtil.get_new_token(region)
        return ApihUtil.tokenMap[region]['accessToken']