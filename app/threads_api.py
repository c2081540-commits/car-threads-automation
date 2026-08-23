from .settings import settings


class ThreadsAPI:
    def __init__(self):
        import requests

        if not settings.threads_user_id or not settings.threads_access_token:
            raise RuntimeError("Threads API認証情報が未設定です")
        self.base = f"https://graph.threads.net/{settings.threads_api_version}"
        self.user_id = settings.threads_user_id
        self.token = settings.threads_access_token
        self.session = requests.Session()

    def _get(self, path, params):
        response = self.session.get(f"{self.base}/{path}", params=params, timeout=(5, 20))
        if not response.ok:
            raise RuntimeError(f"Threads API GET {path} failed: HTTP {response.status_code} body={response.text[:1000]}")
        return response.json()

    def _post(self, path, data):
        response = self.session.post(f"{self.base}/{path}", data=data, timeout=(5, 25))
        if not response.ok:
            raise RuntimeError(f"Threads API POST {path} failed: HTTP {response.status_code} body={response.text[:1000]}")
        return response.json()

    def verify_identity(self):
        result = self._get("me", {"fields": "id,username", "access_token": self.token})
        if str(result.get("id")) != str(self.user_id):
            raise RuntimeError("THREADS_USER_IDとアクセストークンの利用者が一致しません")
        return {"id": str(result["id"]), "username": result.get("username", "")}

    def get_media(self, media_id):
        return self._get(
            str(media_id),
            {
                "fields": "id,text,timestamp,media_type,permalink",
                "access_token": self.token,
            },
        )

    def get_media_insight(self, media_id, metric):
        return self._get(
            f"{media_id}/insights",
            {"metric": metric, "access_token": self.token},
        )

    def _wait_until_ready(self, creation_id, attempts=20, interval=3):
        import time
        for attempt in range(attempts):
            result = self._get(creation_id, {"fields": "status,error_message", "access_token": self.token})
            status = str(result.get("status") or "").upper()
            if status == "FINISHED":
                return
            if status in {"ERROR", "EXPIRED"}:
                raise RuntimeError(f"Threads media container failed: {result}")
            if attempt < attempts - 1:
                time.sleep(interval)
        raise RuntimeError("Threads media container was not ready")

    def _publish_container(self, creation_id, attempts=5, interval=3):
        import time

        last_error = None
        for attempt in range(attempts):
            try:
                result = self._post(
                    f"{self.user_id}/threads_publish",
                    {"access_token": self.token, "creation_id": creation_id},
                )
                return result["id"]
            except RuntimeError as exc:
                last_error = exc
                if "media not found" not in str(exc).lower():
                    raise
                if attempt < attempts - 1:
                    time.sleep(interval)
        raise RuntimeError(f"Threads container publish failed after retry: {last_error}")

    def publish_text(self, text, reply_to_id=None, topic_tag=None):
        payload = {"access_token": self.token, "media_type": "TEXT", "text": text}
        if reply_to_id:
            payload["reply_to_id"] = reply_to_id
        if topic_tag:
            payload["topic_tag"] = topic_tag
        container = self._post(f"{self.user_id}/threads", payload)
        self._wait_until_ready(container["id"])
        return self._publish_container(container["id"])

    def publish_image(self, text, image_url, reply_to_id=None, topic_tag=None):
        payload = {"access_token": self.token, "media_type": "IMAGE", "image_url": image_url, "text": text}
        if reply_to_id:
            payload["reply_to_id"] = reply_to_id
        if topic_tag:
            payload["topic_tag"] = topic_tag
        container = self._post(f"{self.user_id}/threads", payload)
        self._wait_until_ready(container["id"])
        return self._publish_container(container["id"])

    def wait_until_published(self, media_id, attempts=10, interval=2):
        import time
        last = None
        for attempt in range(attempts):
            try:
                result = self._get(media_id, {"fields": "id,permalink,timestamp,text", "access_token": self.token})
                if result.get("permalink"):
                    return result
                last = result
            except Exception as exc:
                last = exc
            if attempt < attempts - 1:
                time.sleep(interval)
        raise RuntimeError(f"Threads公開確認に失敗しました: {last}")
