"""
deployment.yaml の読み込みと 4 階層設定の解決
設計仕様: docs/design/02_ARCHITECTURE_DESIGN.md §4
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ConfigDict
from ruamel.yaml import YAML

PROJECT_ROOT = Path(__file__).parent.parent


class DeploymentConfig(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_version: str = "0.1.0"
    data_root: str = ""
    skills_root: str = "~/.claude/skills"
    domains: list[str] = Field(default_factory=list)
    environment: dict = Field(default_factory=dict)
    deployment: dict = Field(default_factory=dict)


def find_deployment_yaml(start_path: Path | None = None) -> Path:
    """deployment.yaml をプロジェクトルートから上位に向けて探索する。"""
    search = Path(start_path or PROJECT_ROOT)
    for directory in [search, *list(search.parents)]:
        candidate = directory / "deployment.yaml"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "deployment.yaml が見つかりません。"
        "deployment.yaml.template をコピーして deployment.yaml を作成し、"
        "data_root を設定してください。"
    )


def load_deployment_config(config_path: Path | None = None) -> DeploymentConfig:
    """deployment.yaml を読み込んで DeploymentConfig を返す。"""
    if config_path is None:
        config_path = find_deployment_yaml()

    yaml = YAML()
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.load(f)

    return DeploymentConfig.model_validate(raw or {})


def get_data_root(config: DeploymentConfig | None = None) -> Path:
    """data_root を解決して Path を返す。未設定の場合は ValueError を送出する。"""
    if config is None:
        config = load_deployment_config()
    if not config.data_root:
        raise ValueError(
            "deployment.yaml の data_root が未設定です。"
            "Deployment Setup スキルを実行してください。"
        )
    return Path(config.data_root).expanduser().resolve()


def get_museum_data_root(museum_id: str, config: DeploymentConfig | None = None) -> Path:
    """館別データルートパス（{data_root}/museums/{museum_id}）を返す。"""
    return get_data_root(config) / "museums" / museum_id


def load_common_settings() -> dict[str, Any]:
    """common-settings.yaml を読み込む。"""
    path = PROJECT_ROOT / "core" / "policies" / "common-settings.yaml"
    if not path.exists():
        return {}
    yaml = YAML()
    with open(path, encoding="utf-8") as f:
        return yaml.load(f) or {}


def load_domain_settings(domain: str) -> dict[str, Any]:
    """指定ドメインの domain-settings.yaml を読み込む。"""
    path = PROJECT_ROOT / "core" / "knowledge" / "domains" / domain / "domain-settings.yaml"
    if not path.exists():
        return {}
    yaml = YAML()
    with open(path, encoding="utf-8") as f:
        return yaml.load(f) or {}


def resolve_settings(
    museum_profile: dict[str, Any],
    config: DeploymentConfig | None = None,
) -> dict[str, Any]:
    """
    4 階層設定を解決して統合設定 dict を返す。
    優先順位: common(①) < domain(②) < museum-profile(③) < project-brief(④)
    上位（①②）の安全制約は下位から解除不可（将来実装）。
    """
    if config is None:
        config = load_deployment_config()

    merged: dict[str, Any] = {}

    # ① 共通設定
    merged.update(load_common_settings())

    # ② 専門分野別設定（複数ドメイン対応）
    domains = museum_profile.get("basic", {}).get("domains", config.domains)
    for domain in domains:
        domain_cfg = load_domain_settings(domain)
        _deep_merge(merged, domain_cfg)

    # ③ 館別設定（museum-profile）
    _deep_merge(merged, museum_profile)

    return merged


def _deep_merge(base: dict, override: dict) -> None:
    """override を base にディープマージする（破壊的操作）。"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
