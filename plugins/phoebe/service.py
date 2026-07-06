# -*- coding: utf-8 -*-
"""菲比搜索，移植自 NcatBot/plugins/PhoebeSearch"""
from __future__ import annotations

import tempfile
import time
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import requests

MEMES_JSON_URL = "https://phoebehub.top/data/memes.json"
BASE_URL = "https://phoebehub.top/"
MAX_RESULTS = 5
MIN_SCORE = 30.0
CACHE_TTL_SEC = 3600

_HELP = (
    "菲比搜索用法：菲比搜索 <关键词>\n"
    "示例：菲比搜索 2000元烧鸡哈哈\n"
    "数据来源：Phoebe Hub (https://phoebehub.top/)"
)


@dataclass(frozen=True)
class MemeEntry:
    title: str
    url: str


@dataclass(frozen=True)
class SearchHit:
    meme: MemeEntry
    score: float


class PhoebeService:
    def __init__(self) -> None:
        self._memes: list[MemeEntry] = []
        self._cache_loaded_at = 0.0
        self.session = requests.Session()

    def ensure_memes(self) -> None:
        now = time.monotonic()
        if self._memes and now - self._cache_loaded_at < CACHE_TTL_SEC:
            return
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            ),
        }
        response = self.session.get(MEMES_JSON_URL, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        payload = response.json()
        entries: list[MemeEntry] = []
        for item in payload.get("memes", []):
            title = str(item.get("title", "")).strip()
            url = str(item.get("url", "")).strip()
            if title and url:
                entries.append(MemeEntry(title=title, url=url))
        self._memes = entries
        self._cache_loaded_at = now

    @staticmethod
    def _similarity(query: str, title: str) -> float:
        q, t = query.strip(), title.strip()
        if not q or not t:
            return 0.0
        if q == t:
            return 100.0
        if q in t:
            return min(100.0, 80.0 + 20.0 * len(q) / len(t))
        if t in q:
            return min(95.0, 70.0 + 25.0 * len(t) / len(q))
        return SequenceMatcher(None, q, t).ratio() * 100.0

    def search(self, query: str) -> list[SearchHit]:
        hits: list[SearchHit] = []
        for meme in self._memes:
            score = self._similarity(query, meme.title)
            if score >= MIN_SCORE:
                hits.append(SearchHit(meme=meme, score=score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits

    @staticmethod
    def _image_url(path: str) -> str:
        encoded = "/".join(quote(part, safe="") for part in path.split("/"))
        return f"{BASE_URL}{encoded}"

    def _download_image(self, url: str) -> Optional[Path]:
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            suffix = ".gif" if url.lower().endswith(".gif") else ".png"
            fd, name = tempfile.mkstemp(suffix=suffix, prefix="phoebe_")
            path = Path(name)
            with open(fd, "wb") as f:
                f.write(resp.content)
            return path
        except requests.RequestException:
            return None

    def handle_query(self, query: str) -> tuple[str, list[Path]]:
        if not query:
            return _HELP, []
        self.ensure_memes()
        hits = self.search(query)
        if not hits:
            return f"[Phoebe] 未找到与「{query}」匹配的菲比", []
        shown = hits[:MAX_RESULTS]
        lines = [f"[Phoebe] 共找到 {len(hits)} 条，显示前 {len(shown)} 条："]
        images: list[Path] = []
        for idx, hit in enumerate(shown, start=1):
            lines.append(f"{idx}. {hit.meme.title} 相似度 {hit.score:.0f}%")
            url = self._image_url(hit.meme.url)
            img = self._download_image(url)
            if img:
                images.append(img)
        return "\n".join(lines), images


_service: Optional[PhoebeService] = None


def get_service() -> PhoebeService:
    global _service
    if _service is None:
        _service = PhoebeService()
    return _service
