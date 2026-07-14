"""
飞书多维表服务
用于税检康线索提交等场景
"""
import os
import json
import time
import requests
from typing import Dict, Any, Optional


class FeishuBitableService:
    """飞书多维表服务类"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or os.getenv("FEISHU_APP_ID", "")
        self.app_secret = app_secret or os.getenv("FEISHU_APP_SECRET", "")
        self._tenant_access_token = None
        self._token_expire_time = 0

    def _get_tenant_access_token(self) -> str:
        """获取租户访问令牌，带缓存"""
        if self._tenant_access_token and time.time() < self._token_expire_time - 60:
            return self._tenant_access_token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                self._tenant_access_token = data["tenant_access_token"]
                self._token_expire_time = time.time() + data.get("expire", 7200)
                return self._tenant_access_token
            else:
                raise Exception(f"获取飞书token失败: {data.get('msg')}")
        except Exception as e:
            raise Exception(f"飞书认证请求失败: {str(e)}")

    def add_record(self, app_token: str, table_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        新增一条记录到多维表

        Args:
            app_token: 多维表应用 token (base_token)
            table_id: 数据表 ID
            fields: 字段数据字典

        Returns:
            创建的记录信息
        """
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {"fields": fields}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("record", {})
            else:
                raise Exception(f"飞书新增记录失败: {data.get('msg')}, code: {data.get('code')}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"飞书API请求异常: {str(e)}")

    def batch_add_records(self, app_token: str, table_id: str, records: list) -> list:
        """
        批量新增记录

        Args:
            app_token: 多维表应用 token
            table_id: 数据表 ID
            records: 记录列表，每个元素是fields字典

        Returns:
            创建的记录列表
        """
        token = self._get_tenant_access_token()
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "records": [{"fields": r} for r in records]
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("records", [])
            else:
                raise Exception(f"飞书批量新增失败: {data.get('msg')}, code: {data.get('code')}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"飞书API请求异常: {str(e)}")


# 单例
_bitable_service: Optional[FeishuBitableService] = None


def get_bitable_service() -> FeishuBitableService:
    """获取飞书多维表服务单例"""
    global _bitable_service
    if not _bitable_service:
        _bitable_service = FeishuBitableService()
    return _bitable_service
