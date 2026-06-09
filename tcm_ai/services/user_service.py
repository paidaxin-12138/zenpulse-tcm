# Copyright (c) 2026 paidaxin-12138
# Licensed under CC BY-NC 4.0 — see LICENSE in repository root.
# https://creativecommons.org/licenses/by-nc/4.0/

"""微信小程序用户存储。"""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tcm_ai.core.json_io import read_json_file, update_json_file, write_json_file
from tcm_ai.core.paths import DATA_DIR

USERS_PATH = os.path.join(DATA_DIR, "wx_users.json")


class WxUserService:
    def _ensure_file(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(USERS_PATH):
            self._write([])

    def _read(self) -> List[Dict[str, Any]]:
        self._ensure_file()
        data = read_json_file(USERS_PATH, [])
        return data if isinstance(data, list) else []

    def _write(self, users: List[Dict[str, Any]]) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)
        write_json_file(USERS_PATH, users)

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        for user in self._read():
            if user.get("id") == user_id:
                return user
        return None

    def get_by_openid(self, openid: str) -> Optional[Dict[str, Any]]:
        for user in self._read():
            if user.get("openid") == openid:
                return user
        return None

    def upsert_by_openid(
        self,
        openid: str,
        *,
        unionid: Optional[str] = None,
        session_key: Optional[str] = None,  # noqa: ARG002 — 不落盘，仅兼容调用方
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")

        def _upsert(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(users, list):
                users = []
            for user in users:
                if user.get("openid") == openid:
                    user["last_login_at"] = now
                    if unionid:
                        user["unionid"] = unionid
                    user.pop("session_key", None)
                    return users
            suffix = openid[-6:] if len(openid) >= 6 else openid
            users.append(
                {
                    "id": str(uuid.uuid4()),
                    "openid": openid,
                    "unionid": unionid or "",
                    "nick_name": f"微信用户{suffix}",
                    "avatar_url": "",
                    "created_at": now,
                    "last_login_at": now,
                }
            )
            return users

        self._ensure_file()
        update_json_file(USERS_PATH, [], _upsert)
        user = self.get_by_openid(openid)
        if not user:
            raise RuntimeError("用户写入失败")
        return user

    def update_profile(
        self,
        user_id: str,
        *,
        nick_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        cloud_history_index_file_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        updated: Dict[str, Any] = {}

        def _apply(users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            if not isinstance(users, list):
                users = []
            for user in users:
                if user.get("id") != user_id:
                    continue
                if nick_name is not None:
                    user["nick_name"] = nick_name.strip() or user.get("nick_name", "")
                if avatar_url is not None:
                    user["avatar_url"] = avatar_url.strip()
                if cloud_history_index_file_id is not None:
                    user["cloud_history_index_file_id"] = cloud_history_index_file_id.strip()
                updated.clear()
                updated.update(user)
                return users
            return users

        self._ensure_file()
        update_json_file(USERS_PATH, [], _apply)
        return updated or None

    @staticmethod
    def public_view(user: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": user.get("id", ""),
            "nickName": user.get("nick_name") or "微信用户",
            "avatarUrl": user.get("avatar_url") or "",
            "cloudHistoryIndexFileId": user.get("cloud_history_index_file_id") or "",
            "createdAt": user.get("created_at", ""),
            "lastLoginAt": user.get("last_login_at", ""),
        }
