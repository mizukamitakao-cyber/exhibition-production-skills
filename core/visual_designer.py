"""
展示パネルレイアウト試作生成。
Exhibition Visual Designer スキルのPythonサポート。

外部依存なしで動作する単一ファイルHTML/CSS形式の試作を生成する。
"""
from __future__ import annotations

import re
from pathlib import Path

from core.storage import atomic_write


_PANEL_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{panel_id} — {title}</title>
  <style>
    :root {{
      --panel-width: {panel_width};
      --panel-height: {panel_height};
      --bg-color: {bg_color};
      --text-color: {text_color};
      --accent-color: {accent_color};
      --title-font-size: {title_font_size};
      --body-font-size: {body_font_size};
      --line-height: {line_height};
      --padding: {padding};
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      display: flex;
      justify-content: center;
      align-items: flex-start;
      min-height: 100vh;
      background: #e8e8e8;
      padding: 24px;
      font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', sans-serif;
    }}

    .panel {{
      width: var(--panel-width);
      min-height: var(--panel-height);
      background: var(--bg-color);
      color: var(--text-color);
      padding: var(--padding);
      box-shadow: 0 4px 16px rgba(0,0,0,0.18);
    }}

    .panel-header {{
      border-bottom: 3px solid var(--accent-color);
      padding-bottom: 12px;
      margin-bottom: 20px;
    }}

    .panel-id {{
      font-size: 11px;
      color: #888;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }}

    .panel-title {{
      font-size: var(--title-font-size);
      font-weight: 700;
      line-height: 1.3;
      color: var(--text-color);
    }}

    .panel-body {{
      font-size: var(--body-font-size);
      line-height: var(--line-height);
    }}

    .panel-body p {{
      margin-bottom: 1em;
    }}

    .panel-body h2 {{
      font-size: calc(var(--body-font-size) * 1.1);
      font-weight: 600;
      margin: 1.2em 0 0.5em;
      color: var(--accent-color);
    }}

    .panel-body strong {{
      font-weight: 700;
    }}

    .panel-footer {{
      margin-top: 24px;
      padding-top: 10px;
      border-top: 1px solid #ddd;
      font-size: 11px;
      color: #aaa;
    }}

    /* 印刷用スタイル */
    @media print {{
      body {{ background: white; padding: 0; }}
      .panel {{ box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <div class="panel">
    <div class="panel-header">
      <div class="panel-id">{panel_id}</div>
      <h1 class="panel-title">{title}</h1>
    </div>
    <div class="panel-body">
      {body_html}
    </div>
    <div class="panel-footer">{footer}</div>
  </div>
</body>
</html>
"""

_DEFAULT_SPECS: dict = {
    "panel_width": "800px",
    "panel_height": "auto",
    "bg_color": "#ffffff",
    "text_color": "#1a1a1a",
    "accent_color": "#2c5f8a",
    "title_font_size": "26px",
    "body_font_size": "16px",
    "line_height": "1.9",
    "padding": "36px 40px",
}


def _merge_specs(panel_specs: dict) -> dict:
    """館プロファイルの panel_specs とデフォルト値をマージする。"""
    merged = dict(_DEFAULT_SPECS)
    merged.update({k: str(v) for k, v in panel_specs.items() if v})
    return merged


def _md_to_html_body(md: str) -> str:
    """基本的な Markdown → HTML 変換（外部ライブラリ不使用）。"""
    # コードブロックを除去
    md = re.sub(r"```.*?```", "", md, flags=re.DOTALL)
    # 先頭のH1タイトル行を除去（panel_title として別途使用）
    md = re.sub(r"^#\s+.+\n?", "", md, count=1)
    # H2見出し
    md = re.sub(r"^##\s+(.+)$", r"<h2>\1</h2>", md, flags=re.MULTILINE)
    # 太字
    md = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", md)
    # パラグラフ（空行で区切る）
    paragraphs = re.split(r"\n{2,}", md.strip())
    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para.startswith("<h2>"):
            html_parts.append(para)
        else:
            # 単一改行を空白に変換してパラグラフ化
            para = para.replace("\n", " ")
            html_parts.append(f"<p>{para}</p>")
    return "\n      ".join(html_parts)


def generate_panel_html(
    panel_id: str,
    title: str,
    markdown_content: str,
    panel_specs: dict | None = None,
    footer: str = "",
) -> str:
    """展示パネルの HTML を生成する。"""
    specs = _merge_specs(panel_specs or {})
    body_html = _md_to_html_body(markdown_content)
    return _PANEL_HTML_TEMPLATE.format(
        panel_id=panel_id,
        title=title,
        body_html=body_html,
        footer=footer,
        **specs,
    )


def get_design_dir(project_dir: Path) -> Path:
    return project_dir / "design"


def save_design_concept(project_dir: Path, content: str) -> Path:
    """デザインコンセプト文書を保存する。"""
    design_dir = get_design_dir(project_dir)
    design_dir.mkdir(exist_ok=True)
    path = design_dir / "concept.md"
    atomic_write(path, content)
    return path


def save_panel_layout(project_dir: Path, panel_id: str, html: str) -> Path:
    """パネルHTMLレイアウト試作を保存する。"""
    design_dir = get_design_dir(project_dir)
    design_dir.mkdir(exist_ok=True)
    path = design_dir / f"panel-{panel_id}.html"
    atomic_write(path, html)
    return path


def load_panel_layout(project_dir: Path, panel_id: str) -> str | None:
    path = get_design_dir(project_dir) / f"panel-{panel_id}.html"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def list_layouts(project_dir: Path) -> list[dict]:
    design_dir = get_design_dir(project_dir)
    if not design_dir.exists():
        return []
    result = []
    for f in sorted(design_dir.glob("panel-*.html")):
        panel_id = f.stem.removeprefix("panel-")
        result.append({"panel_id": panel_id, "path": str(f)})
    return result
