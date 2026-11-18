"""YAML読み書きユーティリティ。ruamel.yaml + Pydantic v2 を使用。"""
from __future__ import annotations

import io
from pathlib import Path
from typing import TypeVar, Type

from pydantic import BaseModel
from ruamel.yaml import YAML

from core.storage import atomic_write

T = TypeVar("T", bound=BaseModel)

_yaml = YAML()
_yaml.preserve_quotes = True
_yaml.default_flow_style = False
_yaml.width = 4096


def load_yaml(path: Path, model_class: Type[T]) -> T:
    """YAMLファイルを読み込み、Pydanticモデルでバリデーションして返す。"""
    with open(path, "r", encoding="utf-8") as f:
        data = _yaml.load(f)
    return model_class.model_validate(data or {})


def save_yaml(path: Path, model: BaseModel) -> None:
    """PydanticモデルをアトミックにYAMLファイルへ書き込む。"""
    stream = io.StringIO()
    _yaml.dump(model.model_dump(mode="json"), stream)
    atomic_write(path, stream.getvalue())


def load_yaml_raw(path: Path) -> dict:
    """バリデーションなしでYAMLを読み込む（questions.yaml等の非Pydanticデータ用）。"""
    with open(path, "r", encoding="utf-8") as f:
        return _yaml.load(f) or {}
