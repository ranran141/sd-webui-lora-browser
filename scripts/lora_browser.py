import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from modules.script_callbacks import on_app_started, on_ui_tabs

WEBUI_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LORA_DIR = WEBUI_ROOT / "models" / "Lora"
CONFIG_FILE = Path(__file__).resolve().parent / "config.json"

def _load_config():
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _save_config(data: dict):
    cfg = _load_config()
    cfg.update(data)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
HTML_PAGE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>LORA Browser</title>
<style>
:root {
  --bg:#111827; --bg2:#1f2937; --bg3:#0d1117; --bg4:#1a2234; --bg4h:#243047;
  --bd:#374151; --bd2:#4b5563;
  --txt:#f9fafb; --txt2:#d1d5db; --txt3:#9ca3af; --txt4:#6b7280; --txt5:#4b5563;
  --acc:#e2e8f0; --pri:#94a3b8; --pri-bg:rgba(148,163,184,0.12); --pri-bg2:rgba(148,163,184,0.22);
  --fav:#f59e0b; --fav2:#fbbf24; --fav-bg:rgba(245,158,11,0.1);
  --shadow:rgba(0,0,0,0.6);
}
@media (prefers-color-scheme: light) {
  :root {
    --bg:#f3f4f6; --bg2:#ffffff; --bg3:#f9fafb; --bg4:#e5e7eb; --bg4h:#d1d5db;
    --bd:#e5e7eb; --bd2:#d1d5db;
    --txt:#111827; --txt2:#374151; --txt3:#6b7280; --txt4:#9ca3af; --txt5:#d1d5db;
    --acc:#1e293b; --pri:#64748b; --pri-bg:rgba(100,116,139,0.1); --pri-bg2:rgba(100,116,139,0.2);
    --fav:#d97706; --fav2:#f59e0b; --fav-bg:rgba(217,119,6,0.1);
    --shadow:rgba(0,0,0,0.2);
  }
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--txt); font-family: 'Segoe UI', sans-serif;
  font-size: 15px; height: 100vh; display: flex; overflow: hidden; }
#main { display: flex; flex-direction: column; flex: 1; overflow: hidden; }

/* ── ヘッダー ── */
#header { background: var(--bg2); padding: 8px 16px; flex-shrink: 0;
  box-shadow: 0 2px 10px var(--shadow);
  display: flex; gap: 8px; align-items: center; z-index: 100; }
#search { width: 220px; height: 34px; padding: 0 12px;
  background: var(--bg3); border: 1px solid var(--bd2); border-radius: 6px;
  color: var(--txt); font-size: 15px; box-sizing: border-box; flex-shrink: 0; }
#search:focus { outline: none; border-color: var(--pri); }
#weight-wrap { display: flex; align-items: center; gap: 6px; font-size: 14px;
  color: var(--txt3); white-space: nowrap; }
#weight-input { width: 62px; padding: 7px 8px; background: var(--bg3);
  border: 1px solid var(--bd2); border-radius: 6px; color: var(--txt);
  font-size: 14px; text-align: center; }
#count { font-size: 13px; color: var(--txt4); white-space: nowrap; }
.lora-syntax-row { display: flex; align-items: center; gap: 6px; }
.lora-syntax-row .lora-syntax-box { flex: 1; margin: 0; }
.lora-weight-input { width: 66px; padding: 6px 6px; background: var(--bg3);
  border: 1px solid var(--bd2); border-radius: 6px; color: var(--txt);
  font-size: 13px; text-align: center; flex-shrink: 0; }
.lora-weight-input:focus { outline: none; border-color: var(--pri); }
.lora-weight-input::-webkit-inner-spin-button,
.lora-weight-input::-webkit-outer-spin-button { opacity: 1; cursor: pointer; }
.lora-send-btn { width: 34px; height: 34px; border-radius: 7px; border: 1px solid var(--bd2);
  background: var(--bg3); color: var(--txt3); font-size: 14px; cursor: pointer;
  transition: all 0.15s; flex-shrink: 0; }
.lora-send-btn:hover { border-color: var(--pri); background: var(--pri-bg); color: var(--acc); }
.lora-send-btn.sent { border-color: #ef4444; background: rgba(239,68,68,0.1); color: #f87171; }

.hdr-btn { height: 34px; padding: 0 12px; background: var(--bg4); border: 1px solid var(--bd2);
  border-radius: 8px; color: var(--txt3); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; white-space: nowrap; box-sizing: border-box; }
.hdr-btn:hover { background: var(--bg4h); color: var(--txt); }
.hdr-btn.active { border-color: var(--pri); color: var(--acc); background: var(--pri-bg); }
#sidebar-toggle-btn.active { border-color: var(--pri); color: var(--acc); background: var(--pri-bg); }
#sort-by { height: 34px; padding: 0 8px; background: var(--bg3); border: 1px solid var(--bd2);
  border-radius: 6px; color: var(--txt); font-size: 13px; cursor: pointer; box-sizing: border-box; }
#sort-by:focus { outline: none; border-color: var(--pri); }

/* ── 本体レイアウト ── */
#layout { display: flex; flex: 1; overflow: hidden; }

/* ── サイドバー ── */
#sidebar { width: 190px; flex-shrink: 0; background: var(--bg2);
  border-right: 1px solid var(--bd); display: flex; flex-direction: column;
  overflow: hidden; transition: width 0.2s, opacity 0.2s; }
#sidebar.hidden { width: 0; opacity: 0; pointer-events: none; }
#sidebar-title { padding: 10px 14px 8px; font-size: 11px; font-weight: 700;
  letter-spacing: 1px; color: var(--txt4); text-transform: uppercase;
  border-bottom: 1px solid var(--bd); flex-shrink: 0; white-space: nowrap; }
.stree-folder-actions { display: flex; gap: 2px; margin-left: auto; flex-shrink: 0; padding-right: 4px; }
.stree-folder-btn { background: none; border: 1px solid transparent; border-radius: 5px;
  color: var(--txt3); cursor: pointer; font-size: 17px; line-height: 1; padding: 1px 7px;
  transition: all 0.12s; flex-shrink: 0; }
.stree-folder-btn:hover { border-color: var(--pri); color: var(--acc); background: var(--pri-bg); }
.stree-folder-btn.del:hover { border-color: #c55; color: #f66; background: rgba(200,80,80,0.1); }
.fm-inline-create { display: flex; gap: 4px; align-items: center;
  padding: 4px 8px; border-bottom: 1px solid var(--bd); background: var(--bg3); }
#cat-list { overflow-y: auto; flex: 1; padding: 6px 0 240px; min-height: 0; }
.cat-btn { width: 100%; background: none; border: none; cursor: pointer; padding: 0;
  display: flex; align-items: center; text-align: left; transition: background 0.12s; }
.cat-btn:hover { background: var(--pri-bg); }
.cat-btn.active { background: var(--pri-bg2); }
.cat-btn.active .cat-label { color: var(--acc); font-weight: 600; }
.cat-accent { width: 3px; flex-shrink: 0; align-self: stretch;
  border-radius: 0 2px 2px 0; background: transparent; transition: background 0.12s; }
.cat-btn.active .cat-accent { background: var(--pri); }
.cat-inner { flex: 1; display: flex; align-items: center;
  justify-content: space-between; padding: 7px 12px 7px 10px; min-width: 0; }
.cat-label { font-size: 15px; color: var(--txt);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cat-badge { font-size: 12px; background: var(--bg4); color: var(--pri);
  padding: 1px 7px; border-radius: 10px; flex-shrink: 0; font-weight: 600; }
.cat-btn.active .cat-badge { background: var(--pri-bg2); color: var(--acc); }
.sidebar-divider { height: 1px; background: var(--bd); margin: 6px 0; }

/* サイドバーツリー */
.stree-item { }
.stree-row { display: flex; align-items: center; gap: 2px;
  padding: 5px 10px 5px 0; transition: background 0.12s; }
.stree-row:hover { background: var(--pri-bg); }
.stree-row.active { background: var(--pri-bg2); }
.stree-row.active .stree-name { color: var(--acc); font-weight: 600; }
.stree-toggle { width: 20px; height: 20px; background: none; border: none;
  color: var(--txt4); font-size: 8px; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; padding: 0; border-radius: 3px; }
.stree-toggle:hover { color: var(--acc); background: var(--pri-bg); }
.stree-spacer { width: 20px; flex-shrink: 0; }
.stree-name { background: none; border: none; color: var(--txt); font-size: 15px;
  cursor: pointer; text-align: left; flex: 1; white-space: nowrap; overflow: hidden;
  text-overflow: ellipsis; padding: 0; }
.stree-name:hover { color: var(--acc); }
.stree-children { display: none; }
.stree-item.expanded > .stree-children { display: block; }

/* ── コンテンツエリア ── */
#content { flex: 1; overflow-y: auto; padding: 16px 16px 240px;
  display: flex; flex-direction: column; gap: 20px; }

/* ── セクションブロック ── */
.section-block { }
.section-grid { display: grid;
  grid-template-columns: repeat(auto-fill, minmax(var(--thumb-min, 160px), 1fr)); gap: 10px; }
.hdr-sep { width: 1px; height: 20px; background: var(--bd2); flex-shrink: 0; align-self: center; }
.section-block.collapsed .section-grid { display: none; }

/* ── カード ── */
.card { position: relative; border-radius: 10px; overflow: hidden; cursor: pointer;
  aspect-ratio: 2 / 3; border: 2px solid transparent;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s, opacity 0.15s;
  background: var(--bg3); }
.card.dragging { opacity: 0.4; transform: scale(0.97); }
.stree-row.drag-over { background: var(--pri-bg2); outline: 2px dashed var(--pri); outline-offset: -2px; border-radius: 6px; }
.card:hover { transform: translateY(-3px);
  box-shadow: 0 8px 24px var(--pri-bg2); border-color: var(--pri); }
.card.fav-card { border-color: var(--fav); }
.card.fav-card:hover { border-color: var(--fav2); }
.card-img { width: 100%; height: 100%; object-fit: cover; object-position: center top; display: block; }
.card-placeholder { width: 100%; height: 100%; display: flex;
  align-items: center; justify-content: center; font-size: 52px; color: var(--bd2); }
.card-top { position: absolute; top: 0; left: 0; right: 0;
  background: linear-gradient(to bottom, rgba(0,0,0,0.6) 0%, transparent 100%);
  padding: 7px 7px 18px; display: flex; align-items: flex-start;
  justify-content: space-between; opacity: 1; }
.card-base-badge { font-size: 13px; background: rgba(0,0,0,0.52);
  backdrop-filter: blur(4px); color: #e0e0e0; padding: 2px 7px; border-radius: 8px;
  white-space: nowrap; overflow: hidden; max-width: 90px; text-overflow: ellipsis;
  flex-shrink: 0; margin-top: 1px; }
.card-action-btns { display: flex; align-items: center; gap: 3px; flex-shrink: 0; }
.card-folder-btn { background: rgba(0,0,0,0.45); border: none; border-radius: 5px;
  color: #d1d5db; font-size: 13px; cursor: pointer; padding: 2px 5px;
  flex-shrink: 0; transition: color 0.15s, background 0.15s; line-height: 1; }
.card-folder-btn:hover { color: #fff; background: rgba(0,0,0,0.7); }
.card-quick-btn { width: 26px; height: 26px; background: rgba(0,0,0,0.55);
  border: none; border-radius: 50%; cursor: pointer; display: flex;
  align-items: center; justify-content: center; font-size: 12px;
  transition: background 0.15s, transform 0.15s; color: #e0e0e0; padding: 0; }
.card-quick-btn:hover { background: rgba(0,0,0,0.82); transform: scale(1.12); }
.card-fav-btn { width: 26px; height: 26px; background: rgba(0,0,0,0.52);
  backdrop-filter: blur(4px); border: 2px solid transparent; border-radius: 50%; cursor: pointer; display: flex;
  align-items: center; justify-content: center; font-size: 14px; color: #e0e0e0;
  transition: background 0.15s, transform 0.15s, border-color 0.15s; }
.card-fav-btn:hover { background: rgba(0,0,0,0.75); transform: scale(1.15); }
.card-fav-btn.active { color: var(--fav); }
.card-bottom { position: absolute; bottom: 0; left: 0; right: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.88) 0%, rgba(0,0,0,0.55) 60%, transparent 100%);
  padding: 28px 8px 8px; display: flex; align-items: flex-end; justify-content: space-between; gap: 4px; }
.card-name { font-size: 14px; font-weight: 600; color: #fff; line-height: 1.3;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  text-shadow: 0 1px 4px rgba(0,0,0,0.9); }

/* ── モーダル ── */
#modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.75);
  z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 20px; }
#modal { background: var(--bg2); border-radius: 14px; width: 100%; max-width: 900px;
  max-height: 92vh; overflow: hidden; display: flex; flex-direction: column;
  box-shadow: 0 24px 60px var(--shadow); border: 1px solid var(--bd); position: relative; }
#modal-close { position: absolute; top: 12px; right: 12px; width: 32px; height: 32px;
  background: var(--bg4); border: none; border-radius: 50%;
  color: var(--txt3); font-size: 18px; cursor: pointer; display: flex;
  align-items: center; justify-content: center; z-index: 10;
  transition: background 0.15s, color 0.15s; }
#modal-close:hover { background: var(--bg4h); color: var(--txt); }
#modal-head { padding: 18px 20px 14px; border-bottom: 1px solid var(--bd); flex-shrink: 0; }
#modal-model-name { font-size: 22px; font-weight: 700; color: var(--acc);
  margin-bottom: 12px; padding-right: 40px; line-height: 1.3;
  display: flex; align-items: center; gap: 8px; }
#modal-file-name { font-size: 11px; color: var(--txt4); margin-top: 2px; }
#modal-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.modal-action-btn { display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 14px; border-radius: 8px; border: 1px solid var(--bd2);
  background: var(--bg3); color: var(--acc); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.modal-action-btn:hover { border-color: var(--pri); background: var(--pri-bg); }
.modal-action-btn.fav-btn.active { color: var(--fav); border-color: var(--fav); background: var(--fav-bg); }
.modal-action-btn.delete-btn { border-color: #7f1d1d; color: #fca5a5; }
.modal-action-btn.delete-btn:hover { background: rgba(220,38,38,0.15); border-color: #ef4444; color: #fca5a5; }
.si-list { display: flex; flex-wrap: wrap; gap: 8px; }
.si-card { border: 1px solid var(--bd); border-radius: 8px; overflow: hidden;
  background: var(--bg3); width: calc(50% - 4px); min-width: 0; }
.si-img-wrap { position: relative; }
.si-img { width: 100%; height: auto; display: block; }
.si-meta-bar { padding: 6px 8px; border-bottom: 1px solid var(--bd); background: var(--bg4); }
.si-meta-chips { display: flex; flex-wrap: wrap; gap: 4px; }
.si-chip { display: inline-flex; flex-direction: column; align-items: center;
  background: var(--bg2); border: 1px solid var(--bd2); border-radius: 5px;
  padding: 2px 6px; min-width: 36px; }
.si-chip-label { font-size: 10px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.4px; color: var(--txt4); line-height: 1.2; }
.si-chip-val { font-size: 13px; color: var(--txt); line-height: 1.3; }
.si-meta-model { font-size: 12px; color: var(--txt4); margin-top: 5px; }
.si-prompt-row { display: flex; align-items: flex-start; gap: 8px; padding: 8px 10px;
  cursor: pointer; border-top: 1px solid var(--bd); transition: background 0.12s; }
.si-prompt-row:hover { background: var(--pri-bg); }
.si-prompt-row.tw-active { background: var(--pri-bg2); }
.si-prompt-label { font-size: 12px; font-weight: 700; color: var(--txt4);
  text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap;
  width: 52px; flex-shrink: 0; padding-top: 1px; }
.si-prompt-row.tw-active .si-prompt-label { color: var(--acc); }
.si-prompt-text { font-size: 13px; color: var(--txt3); line-height: 1.4; flex: 1;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.si-prompt-row.tw-active .si-prompt-text { color: var(--txt2); }
.civitai-html-wrap { font-size: 13px; color: var(--txt2); line-height: 1.6;
  max-height: 500px; overflow-y: auto; word-break: break-word; }
.civitai-html-wrap p { margin-bottom: 8px; }
.civitai-html-wrap h1,.civitai-html-wrap h2,.civitai-html-wrap h3 {
  font-size: 13px; font-weight: 700; color: var(--acc); margin: 10px 0 4px; }
.civitai-html-wrap img { max-width: 100%; border-radius: 6px; margin: 6px 0; display: block; }
.civitai-html-wrap ul,.civitai-html-wrap ol { padding-left: 16px; margin-bottom: 8px; }
.civitai-html-wrap strong { color: var(--txt); }
.civitai-html-wrap a { color: var(--pri); text-decoration: none; }
.civitai-html-wrap a:hover { text-decoration: underline; }
.modal-action-btn.send-txt { border-color: #1d4ed8; color: #93c5fd; }
.modal-action-btn.send-txt:hover { background: rgba(29,78,216,0.15); border-color: #3b82f6; }
.modal-action-btn.civitai-btn { border-color: #0e7490; color: #67e8f9; }
.modal-action-btn.civitai-btn:hover { background: rgba(14,116,144,0.15); border-color: #06b6d4; }
.modal-action-btn.fetch-btn { border-color: #166534; color: #86efac; }
.modal-action-btn.fetch-btn:hover { background: rgba(22,101,52,0.2); border-color: #22c55e; }
.modal-action-btn.fetch-btn:disabled { opacity: 0.5; cursor: default; }
#bulk-fetch-progress { display: none; flex-direction: column; gap: 8px; }
#bulk-fetch-bar-wrap { background: var(--bg3); border-radius: 6px; height: 8px; overflow: hidden; }
#bulk-fetch-bar { height: 100%; width: 0; background: #22c55e; border-radius: 6px; transition: width 0.2s; }
#bulk-fetch-status { font-size: 13px; color: var(--txt3); min-height: 18px; overflow: hidden;
  text-overflow: ellipsis; white-space: nowrap; }
#bulk-fetch-result { font-size: 13px; color: var(--txt2); min-height: 18px; }
#settings-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: none;
  align-items: center; justify-content: center; z-index: 9000; }
#settings-modal { background: var(--bg2); border: 1px solid var(--bd); border-radius: 12px;
  width: 420px; max-width: 92vw; padding: 24px; display: flex; flex-direction: column; gap: 18px;
  box-shadow: 0 12px 48px var(--shadow); }
#settings-title { font-size: 16px; font-weight: 700; color: var(--acc); }
.settings-row { display: flex; flex-direction: column; gap: 6px; }
.settings-label { font-size: 14px; font-weight: 600; letter-spacing: 0.5px;
  text-transform: uppercase; color: var(--txt); }
.settings-input { background: var(--bg3); border: 1px solid var(--bd); border-radius: 8px;
  color: var(--txt); font-size: 13px; padding: 8px 10px; width: 100%; box-sizing: border-box;
  transition: border-color 0.15s; }
.settings-input:focus { outline: none; border-color: var(--pri); }
.settings-hint { font-size: 12px; color: var(--txt4); font-weight: 400; letter-spacing: 0; text-transform: none; }
#settings-footer { display: flex; gap: 8px; justify-content: flex-end; }
.settings-toggle-row { display: flex; align-items: center; justify-content: space-between; }
.settings-toggle-label { font-size: 14px; color: var(--txt3); font-weight: 400; }
.toggle-switch { position: relative; width: 38px; height: 22px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-track { position: absolute; inset: 0; background: var(--bd2); border-radius: 11px;
  cursor: pointer; transition: background 0.2s; }
.toggle-track::before { content: ''; position: absolute; width: 16px; height: 16px;
  left: 3px; top: 3px; background: white; border-radius: 50%; transition: transform 0.2s; }
.toggle-switch input:checked + .toggle-track { background: var(--pri); }
.toggle-switch input:checked + .toggle-track::before { transform: translateX(16px); }
#modal-body { display: flex; overflow: hidden; flex: 1; min-height: 0; }
#modal-preview-col { width: 200px; flex-shrink: 0; background: var(--bg3);
  display: flex; flex-direction: column; align-items: stretch; overflow: hidden; }
#modal-preview-col img { width: 100%; object-fit: cover; object-position: center top; flex-shrink: 0; }
#modal-preview-col .placeholder { font-size: 48px; color: var(--bd2); text-align: center; padding: 30px 0; }
#preview-img-wrap { position: relative; flex-shrink: 0; }
#preview-change-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.45);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.18s; cursor: pointer; }
#preview-img-wrap:hover #preview-change-overlay { opacity: 1; }
#preview-change-overlay span { background: rgba(0,0,0,0.65); border-radius: 8px;
  color: #fff; font-size: 12px; font-weight: 600; padding: 6px 12px; pointer-events: none; }
#modal-preview-info { padding: 10px 10px; display: flex; flex-direction: column; gap: 8px;
  border-top: 1px solid var(--bd); flex: 1; overflow: hidden; }
.pvi-item { display: flex; flex-direction: column; gap: 2px; }
.pvi-label { font-size: 15px; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.5px; color: var(--txt); }
.pvi-value { font-size: 13px; color: var(--txt3); word-break: break-word; line-height: 1.4; }
.pvi-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 2px; }
.pvi-tag { font-size: 13px; background: var(--pri-bg); border: 1px solid var(--bd2);
  border-radius: 10px; padding: 3px 9px; color: var(--pri); font-weight: 500; }
.file-info-row { display: flex; flex-direction: column; margin-bottom: 6px; }
.file-info-lbl { font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.5px; color: var(--txt4); }
.file-info-val { font-size: 12px; color: var(--txt2); word-break: break-all; line-height: 1.4; }
.file-info-path { color: var(--txt3); font-size: 11px; }
#modal-info-col { flex: 1; overflow-y: auto; padding: 16px 20px; }
.info-section { margin-bottom: 16px; }
.info-label { font-size: 14px; font-weight: 600; letter-spacing: 0.5px;
  text-transform: uppercase; color: var(--txt); margin-bottom: 4px; }
.info-label-hint { display: block; font-size: 12px; color: var(--txt4); font-weight: 400;
  text-transform: none; letter-spacing: 0; margin-top: 2px; margin-left: 0; }
.info-value { font-size: 13px; color: var(--txt2); line-height: 1.5; }
.tags-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
.tag-chip { font-size: 12px; background: var(--bg4); border: 1px solid var(--bd2);
  border-radius: 12px; padding: 3px 10px; color: var(--txt3); }
.lora-syntax-box { background: var(--bg3); border: 1px solid var(--bd); border-radius: 6px;
  padding: 8px 12px; font-family: monospace; font-size: 14px; color: var(--acc); }
.trained-words-wrap { display: flex; flex-direction: column; gap: 5px; }
.trained-word-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: var(--bg3); border: 1px solid var(--bd); border-radius: 7px;
  cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.trained-word-item:hover { border-color: var(--pri); background: var(--pri-bg); }
.trained-word-item.tw-active { border-color: var(--pri); background: var(--pri-bg2); }
.trained-word-text { font-size: 13px; color: #3b82f6; line-height: 1.5;
  word-break: break-word; flex: 1; }
.trained-word-item.tw-active .trained-word-text { color: var(--acc); }
.trained-word-send { display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  color: var(--txt); width: 24px; font-size: 20px; font-weight: 300; line-height: 1; opacity: 0.45; user-select: none; }
.trained-word-item:hover .trained-word-send { color: var(--txt); opacity: 0.8; }
.trained-word-item.tw-active .trained-word-send { color: var(--acc); opacity: 1; }

/* トリガーワード編集UI */
.tw-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.tw-edit-btn { background: var(--bg4); border: 1px solid var(--bd2); border-radius: 7px;
  color: var(--txt2); font-size: 13px; font-weight: 600; cursor: pointer; padding: 4px 14px; transition: all 0.15s; }
.tw-edit-btn:hover { border-color: var(--pri); background: var(--pri-bg); color: var(--acc); }
.tw-edit-row { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }
.tw-edit-input { flex: 1; background: var(--bg3); border: 1px solid var(--bd2);
  border-radius: 6px; color: var(--txt); font-size: 12px; padding: 6px 10px; }
.tw-edit-input:focus { outline: none; border-color: var(--pri); }
.tw-del-btn { background: none; border: 1.5px solid var(--bd2); border-radius: 6px;
  color: var(--txt3); font-size: 20px; font-weight: 700; cursor: pointer;
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; transition: all 0.15s; line-height: 1; }
.tw-del-btn:hover { border-color: #ef4444; color: #ef4444; }
.tw-add-btn { width: 100%; background: none; border: 1.5px dashed var(--bd2);
  border-radius: 6px; color: var(--txt3); font-size: 22px; font-weight: 700; cursor: pointer;
  padding: 4px; transition: all 0.15s; margin-top: 6px; }
.tw-add-btn:hover { border-color: var(--pri); color: var(--acc); }
.tw-edit-actions { display: flex; gap: 8px; margin-top: 10px; }
.tw-save-btn { flex: 1; padding: 7px; border-radius: 7px; border: 1px solid var(--pri);
  background: var(--pri-bg); color: var(--acc); font-size: 12px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; }
.tw-save-btn:hover { background: var(--pri-bg2); }
.tw-cancel-btn { padding: 7px 14px; border-radius: 7px; border: 1px solid var(--bd2);
  background: none; color: var(--txt3); font-size: 12px; font-weight: 600;
  cursor: pointer; transition: all 0.15s; }
.tw-cancel-btn:hover { border-color: var(--txt4); color: var(--txt); }
.icon-action-btn { background: var(--bg4); border: 1px solid var(--bd2); border-radius: 6px;
  color: var(--txt3); cursor: pointer; width: 28px; height: 28px; display: flex;
  align-items: center; justify-content: center; flex-shrink: 0; transition: all 0.15s; padding: 0; }
.icon-action-btn:hover { border-color: var(--pri); background: var(--pri-bg); color: var(--acc); }

/* ── Tags編集オーバーレイ ── */
#tags-edit-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.65);
  display: flex; align-items: center; justify-content: center; z-index: 3000; }
#tags-edit-modal { background: var(--bg2); border: 1px solid var(--bd); border-radius: 12px;
  width: 380px; max-width: 92vw; max-height: 80vh; display: flex; flex-direction: column;
  box-shadow: 0 12px 48px var(--shadow); }
#tags-edit-header { padding: 14px 18px 12px; display: flex; align-items: center;
  justify-content: space-between; border-bottom: 1px solid var(--bd); flex-shrink: 0; }
#tags-edit-title { font-size: 15px; font-weight: 700; color: var(--acc); }
#tags-edit-close { background: none; border: none; color: var(--txt4); font-size: 18px;
  cursor: pointer; padding: 2px 6px; border-radius: 6px; line-height: 1; transition: all 0.15s; }
#tags-edit-close:hover { background: var(--bg4h); color: var(--txt); }
#tags-edit-body { padding: 16px 18px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
#tags-edit-list { display: flex; flex-wrap: wrap; gap: 6px; min-height: 36px;
  padding: 10px; background: var(--bg3); border: 1px solid var(--bd); border-radius: 8px; }
#tags-edit-input-row { display: flex; gap: 6px; }
#tags-edit-footer { padding: 12px 18px; border-top: 1px solid var(--bd);
  display: flex; gap: 8px; flex-shrink: 0; }

/* ── サムネイルサイズ切替 ── */
.sp-btns { display: flex; gap: 6px; }
.sp-btn { width: 34px; height: 34px; border-radius: 8px; border: 1px solid var(--bd2);
  background: var(--bg4); color: var(--txt3); font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.15s; box-sizing: border-box; }
.sp-btn:hover { border-color: var(--pri); color: var(--acc); }
.sp-btn.active { border-color: var(--pri); background: var(--pri-bg2); color: var(--acc); }

/* ── トースト ── */
#toast { position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
  background: var(--pri); color: white; padding: 10px 20px; border-radius: 20px;
  font-size: 14px; opacity: 0; transition: opacity 0.3s; z-index: 9999;
  pointer-events: none; white-space: nowrap; max-width: 90vw;
  overflow: hidden; text-overflow: ellipsis; }
#toast.show { opacity: 1; }
#loading { text-align: center; padding: 60px; color: var(--txt4); font-size: 16px; }

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--bd2); border-radius: 3px; }
</style>
</head>
<body>

<!-- Layout -->
<div id="layout">
  <div id="sidebar">
    <div id="cat-list"></div>
  </div>
  <div id="main">
    <div id="header">
      <input id="search" type="text" placeholder="Search..." oninput="onSearch()">
      <div class="hdr-sep"></div>
      <select id="sort-by" onchange="sortBy=this.value;onSortChange()" title="Sort by">
        <option value="path">Path</option>
        <option value="name">Name</option>
        <option value="date">Added</option>
      </select>
      <button id="sort-dir-btn" class="hdr-btn" onclick="toggleSortDir()" title="Sort direction">↑</button>
      <div style="flex:1"></div>
      <div class="hdr-sep"></div>
      <div class="sp-btns">
        <button class="sp-btn" id="sp-thumb-sm" onclick="setThumbSize('sm')">S</button>
        <button class="sp-btn" id="sp-thumb-md" onclick="setThumbSize('md')">M</button>
        <button class="sp-btn" id="sp-thumb-lg" onclick="setThumbSize('lg')">L</button>
      </div>
      <div class="hdr-sep"></div>
      <button id="sidebar-toggle-btn" class="hdr-btn active" onclick="toggleSidebar()" title="Sidebar">≡</button>
      <button id="refresh-btn" class="hdr-btn" onclick="loadLoras()" title="Refresh">⟳</button>
      <button id="settings-btn" class="hdr-btn" onclick="openSettings()" title="Settings">⚙</button>
    </div>
    <div id="content">
      <div id="loading">Loading...</div>
    </div>
  </div>
</div>

<!-- Settings Overlay -->
<div id="settings-overlay" style="display:none" onclick="onSettingsOverlayClick(event)">
  <div id="settings-modal">
    <div id="settings-title">⚙ Settings</div>
    <div class="settings-row">
      <div class="settings-label">LoRA Folder Path</div>
      <input id="settings-lora-dir" class="settings-input" type="text"
        placeholder="e.g. D:/models/Lora  (leave blank to use WebUI default)">
      <div class="settings-hint">Leave blank to use the WebUI default path. Reload required after change.</div>
    </div>
    <div class="settings-row">
      <div class="settings-label">civitai API Key</div>
      <input id="settings-civitai-key" class="settings-input" type="password"
        placeholder="e.g. xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        autocomplete="off">
      <div class="settings-hint">civitai → Account Settings → API Keys. Basic fetch works without a key.</div>
    </div>
    <div class="settings-row">
      <div class="settings-label">Sidebar</div>
      <div class="settings-toggle-row">
        <span class="settings-toggle-label">Show Favorites</span>
        <label class="toggle-switch"><input type="checkbox" id="settings-show-favs"><span class="toggle-track"></span></label>
      </div>
      <div class="settings-toggle-row">
        <span class="settings-toggle-label">Show Recently Used</span>
        <label class="toggle-switch"><input type="checkbox" id="settings-show-recent"><span class="toggle-track"></span></label>
      </div>
    </div>
    <div class="settings-row">
      <div class="settings-label">civitai Metadata</div>
      <button class="modal-action-btn fetch-btn" id="bulk-fetch-start-btn" style="width:100%;justify-content:center"
        onclick="saveSettingsOnly();startBulkFetch()">☁ Fetch All</button>
    </div>
    <div id="bulk-fetch-progress">
      <div id="bulk-fetch-bar-wrap"><div id="bulk-fetch-bar"></div></div>
      <div id="bulk-fetch-status"></div>
      <div id="bulk-fetch-result"></div>
      <button class="modal-action-btn delete-btn" id="bulk-fetch-stop-btn" onclick="bulkFetchAbort=true" style="align-self:flex-end">■ Stop</button>
    </div>
    <div id="settings-footer">
      <button class="modal-action-btn" onclick="closeSettings()">Close</button>
      <button class="modal-action-btn civitai-btn" onclick="saveSettings()">Save</button>
    </div>
  </div>
</div>

<!-- Modal -->
<div id="modal-overlay" style="display:none" onclick="onOverlayClick(event)">
  <div id="modal">
    <button id="modal-close" onclick="closeModal()">✕</button>
    <div id="modal-head">
      <div id="modal-model-name"></div>
      <div id="modal-actions">
        <button class="modal-action-btn civitai-btn" id="btn-civitai" onclick="openCivitai()" style="display:none">🌐 civitai</button>
        <button class="modal-action-btn fetch-btn" id="btn-fetch-civitai" onclick="fetchCivitai()">🔄 Fetch</button>
        <button class="modal-action-btn delete-btn" onclick="deleteLora()">🗑 Delete</button>
      </div>
    </div>
    <div id="modal-body">
      <div id="modal-preview-col">
        <div id="modal-preview-info"></div>
      </div>
      <div id="modal-info-col"></div>
    </div>
  </div>
</div>

<!-- Tags Edit Overlay -->
<div id="tags-edit-overlay" style="display:none" onclick="onTagsOverlayClick(event)">
  <div id="tags-edit-modal">
    <div id="tags-edit-header">
      <div id="tags-edit-title">Edit Tags</div>
      <button id="tags-edit-close" onclick="cancelEditTags()">✕</button>
    </div>
    <div id="tags-edit-body">
      <div id="tags-edit-list"></div>
      <div id="tags-edit-input-row">
        <input id="tags-edit-input" class="tw-edit-input" style="flex:1;font-size:13px;padding:6px 10px"
          placeholder="Add tag..." onkeydown="if(event.key==='Enter')addTagDraft()">
        <button class="icon-action-btn" onclick="addTagDraft()" title="Add tag" style="width:34px;height:34px"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></button>
      </div>
    </div>
    <div id="tags-edit-footer">
      <button class="tw-save-btn" onclick="saveTagsEdit()" style="flex:2;padding:8px">Save</button>
      <button class="tw-cancel-btn" onclick="cancelEditTags()" style="flex:1;padding:8px">Cancel</button>
    </div>
  </div>
</div>

<div id="toast"></div>

<script>
let allLoras = [];
let allFolders = [];
let activeCat = null;
let currentLora = null;
let sortBy = 'path';
let sortDir = 'asc';
let previewVer = Date.now();
let activeWords = new Map();
let activeSampleSends = new Map();
let currentWeight = 1.0;
let sentLoraText = null;

const THUMB_SIZES = { sm: 120, md: 160, lg: 210 };

/* ── 設定 ── */
function getSetting(key, def) {
  return localStorage.getItem('lora_cfg_' + key) || def;
}
function setSetting(key, val) {
  localStorage.setItem('lora_cfg_' + key, val);
}

function initSettings() {
  setThumbSize(getSetting('thumb_size', 'md'), true);
  const sidebarVisible = getSetting('sidebar', '1') === '1';
  setSidebarVisible(sidebarVisible);
}

function setThumbSize(size, silent) {
  setSetting('thumb_size', size);
  document.documentElement.style.setProperty('--thumb-min', (THUMB_SIZES[size] || 160) + 'px');
  document.querySelectorAll('[id^="sp-thumb-"]').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById('sp-thumb-' + size);
  if (btn) btn.classList.add('active');
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const visible = sidebar.classList.contains('hidden');
  setSidebarVisible(visible);
}

function setSidebarVisible(visible) {
  const sidebar = document.getElementById('sidebar');
  const btn = document.getElementById('sidebar-toggle-btn');
  sidebar.classList.toggle('hidden', !visible);
  btn.classList.toggle('active', visible);
  setSetting('sidebar', visible ? '1' : '0');
}


/* ── データ読み込み ── */
async function loadLoras() {
  previewVer = Date.now();
  try {
    const res = await fetch('/lora_browser/list', {cache: 'no-store'});
    const data = await res.json();
    allLoras = Array.isArray(data) ? data : (data.loras || []);
    allFolders = Array.isArray(data) ? [] : (data.folders || []);
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.remove();
    const content = document.getElementById('content');
    content.innerHTML = '';
    buildSections();
    document.getElementById('cat-list').innerHTML = '';
    buildSidebar();
    restoreActiveCat();
    applyFilter();
  } catch(e) {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) loadingEl.textContent = 'Failed to load: ' + e.message;
    else console.error('loadLoras failed:', e);
  }
}
function restoreActiveCat() {
  if (activeCat === null) return;
  const allBtn = document.getElementById('all-sidebar-btn');
  if (allBtn) allBtn.classList.remove('active');
  if (activeCat === '__fav__') {
    const favBtn = document.getElementById('fav-sidebar-btn');
    if (favBtn) favBtn.classList.add('active');
  } else {
    document.querySelectorAll('.stree-row[data-cat]').forEach(row => {
      if (row.dataset.cat === activeCat) row.classList.add('active');
    });
  }
}

/* ── セクション構築 ── */
function getSortedLoras(loras) {
  return [...loras].sort((a, b) => {
    let va, vb;
    if (sortBy === 'name') {
      va = (a.model_name || a.name || '').toLowerCase();
      vb = (b.model_name || b.name || '').toLowerCase();
    } else if (sortBy === 'date') {
      va = a.file_date || 0; vb = b.file_date || 0;
    } else {
      va = (a.file_path || '').toLowerCase(); vb = (b.file_path || '').toLowerCase();
    }
    if (va < vb) return sortDir === 'asc' ? -1 : 1;
    if (va > vb) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });
}
function onSortChange() {
  setSetting('sort_by', sortBy);
  setSetting('sort_dir', sortDir);
  const content = document.getElementById('content');
  content.innerHTML = '';
  buildSections();
  applyFilter();
}
function toggleSortDir() {
  sortDir = sortDir === 'asc' ? 'desc' : 'asc';
  const btn = document.getElementById('sort-dir-btn');
  if (btn) btn.textContent = sortDir === 'asc' ? '↑' : '↓';
  onSortChange();
}
function buildSections() {
  const content = document.getElementById('content');
  const block = document.createElement('div');
  block.className = 'section-block';
  const grid = document.createElement('div');
  grid.className = 'section-grid';
  getSortedLoras(allLoras).forEach(lora => grid.appendChild(makeCard(lora)));
  block.appendChild(grid);
  content.appendChild(block);
}

/* ── サイドバー構築 ── */
function rebuildSidebar() {
  const list = document.getElementById('cat-list');
  list.innerHTML = '';
  buildSidebar();
  applyFilter();
}
function buildSidebar() {
  const list = document.getElementById('cat-list');
  const showFavs = getSetting('show_favs', '1') === '1';
  const showRecent = getSetting('show_recent', '1') === '1';

  if (showRecent) {
    const recentBtn = makeFlatBtn('__recent__', '🕐 Recently Used', getRecent().length);
    recentBtn.id = 'recent-sidebar-btn';
    list.appendChild(recentBtn);
  }
  if (showFavs) {
    const favBtn = makeFlatBtn('__fav__', '⭐ Favorites', getFavs().length);
    favBtn.id = 'fav-sidebar-btn';
    list.appendChild(favBtn);
  }
  if (showRecent || showFavs) {
    list.appendChild(Object.assign(document.createElement('div'), { className: 'sidebar-divider' }));
  }

  const allBtn = document.createElement('button');
  allBtn.className = 'cat-btn';
  allBtn.id = 'all-sidebar-btn';
  allBtn.dataset.cat = '';
  allBtn.innerHTML =
    `<div class="cat-accent"></div>` +
    `<div class="cat-inner">` +
    `<span class="cat-label">All</span>` +
    `<button class="stree-folder-btn" title="Create root folder" style="font-size:17px;padding:1px 7px" ` +
    `onclick="event.stopPropagation();showInlineRootCreate()">+</button>` +
    `</div>`;
  allBtn.addEventListener('click', () => setCat('', allBtn));
  allBtn.classList.add('active');
  list.appendChild(allBtn);

  const tree = buildCatTree();
  renderSidebarNode(tree, list, 0);
}

function buildCatTree() {
  const root = { dirs: {}, total: allLoras.length };
  allFolders.forEach(folder => {
    const parts = folder.split('/').filter(Boolean);
    let node = root;
    parts.forEach(part => {
      if (!node.dirs[part]) node.dirs[part] = { dirs: {}, count: 0, path: '' };
      node = node.dirs[part];
    });
  });
  allLoras.forEach(lora => {
    if (!lora.category) return;
    const parts = lora.category.split('/').filter(Boolean);
    let node = root;
    parts.forEach((part, i) => {
      if (!node.dirs[part]) node.dirs[part] = { dirs: {}, count: 0, path: '' };
      node = node.dirs[part];
      node.count = (node.count || 0) + 1;
    });
  });
  function setPaths(node, prefix) {
    Object.entries(node.dirs).forEach(([name, child]) => {
      child.path = prefix ? prefix + '/' + name : name;
      setPaths(child, child.path);
    });
  }
  setPaths(root, '');
  return root;
}

function addFolderActions(row, folderPath) {
  const wrap = document.createElement('span');
  wrap.className = 'stree-folder-actions';
  const addBtn = document.createElement('button');
  addBtn.className = 'stree-folder-btn';
  addBtn.title = 'Create subfolder';
  addBtn.textContent = '+';
  addBtn.addEventListener('click', e => { e.stopPropagation(); showInlineCreateFolder(row, folderPath); });
  const delBtn = document.createElement('button');
  delBtn.className = 'stree-folder-btn del';
  delBtn.title = 'Delete folder';
  delBtn.textContent = '×';
  delBtn.addEventListener('click', e => { e.stopPropagation(); confirmDeleteFolder(folderPath); });
  wrap.appendChild(addBtn);
  wrap.appendChild(delBtn);
  row.appendChild(wrap);
}
function showInlineRootCreate() {
  const existing = document.getElementById('fm-inline-create');
  if (existing) { existing.remove(); return; }
  const catList = document.getElementById('cat-list');
  const div = document.createElement('div');
  div.id = 'fm-inline-create';
  div.className = 'fm-inline-create';
  div.style.paddingLeft = '10px';
  const inp = document.createElement('input');
  inp.className = 'tw-edit-input';
  inp.placeholder = 'New folder name';
  inp.style.cssText = 'flex:1;font-size:12px;padding:3px 7px';
  const cancel = document.createElement('button');
  cancel.className = 'stree-folder-btn';
  cancel.textContent = '×';
  cancel.addEventListener('click', () => div.remove());
  inp.addEventListener('keydown', async e => {
    if (e.key === 'Enter') {
      const name = inp.value.trim().replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
      if (!name) return;
      div.remove();
      await createFolder(name);
    }
    if (e.key === 'Escape') div.remove();
  });
  div.appendChild(inp);
  div.appendChild(cancel);
  const allBtn = document.getElementById('all-sidebar-btn');
  const ref = allBtn ? allBtn.nextSibling : catList.firstChild;
  catList.insertBefore(div, ref);
  inp.focus();
}
function showInlineCreateFolder(row, parentPath) {
  const existing = document.getElementById('fm-inline-create');
  if (existing) { existing.remove(); return; }
  const div = document.createElement('div');
  div.id = 'fm-inline-create';
  div.className = 'fm-inline-create';
  div.style.paddingLeft = (parseInt(row.style.paddingLeft) + 16) + 'px';
  const inp = document.createElement('input');
  inp.className = 'tw-edit-input';
  inp.placeholder = 'New folder name';
  inp.style.cssText = 'flex:1;font-size:12px;padding:3px 7px';
  const cancel = document.createElement('button');
  cancel.className = 'stree-folder-btn';
  cancel.textContent = '×';
  cancel.addEventListener('click', () => div.remove());
  inp.addEventListener('keydown', async e => {
    if (e.key === 'Enter') {
      const name = inp.value.trim().replace(/\\/g, '/').replace(/^\/+|\/+$/g, '');
      if (!name) return;
      const fullPath = parentPath ? parentPath + '/' + name : name;
      div.remove();
      await createFolder(fullPath);
    }
    if (e.key === 'Escape') div.remove();
  });
  div.appendChild(inp);
  div.appendChild(cancel);
  row.parentElement.insertBefore(div, row.nextSibling);
  inp.focus();
}
async function createFolder(path) {
  try {
    const res = await fetch('/lora_browser/create_folder', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({path})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed');
    showToast('Created: ' + path);
    await loadLoras();
  } catch(e) { showToast('Error: ' + e.message); }
}
async function confirmDeleteFolder(folderPath) {
  const counts = {};
  allLoras.forEach(l => { if (l.category) counts[l.category] = (counts[l.category] || 0) + 1; });
  if (counts[folderPath] > 0) { showToast('Folder is not empty'); return; }
  if (!confirm('Delete folder "' + folderPath + '"?')) return;
  try {
    const res = await fetch('/lora_browser/delete_folder', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({path: folderPath})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Failed');
    activeCat = null;
    showToast('Deleted: ' + folderPath);
    await loadLoras();
  } catch(e) { showToast('Error: ' + e.message); }
}
function addFolderDrop(el, folderPath) {
  el.addEventListener('dragover', e => {
    if (!e.dataTransfer.types.includes('text/lora-name')) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    el.classList.add('drag-over');
  });
  el.addEventListener('dragleave', e => {
    if (!el.contains(e.relatedTarget)) el.classList.remove('drag-over');
  });
  el.addEventListener('drop', async e => {
    e.preventDefault();
    el.classList.remove('drag-over');
    const name = e.dataTransfer.getData('text/lora-name');
    if (!name) return;
    await moveLora(name, folderPath);
  });
}
async function moveLora(name, targetFolder) {
  try {
    const res = await fetch('/lora_browser/move_lora', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name, target_folder: targetFolder})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Move failed');
    showToast('Moved to ' + (targetFolder || 'root'));
    closeModal();
    loadLoras();
  } catch(e) { showToast('Error: ' + e.message); }
}
function renderSidebarNode(node, container, depth) {
  Object.keys(node.dirs).sort((a, b) => a.localeCompare(b, 'ja')).forEach(dirName => {
    const child = node.dirs[dirName];
    const hasChildren = Object.keys(child.dirs).length > 0;

    const item = document.createElement('div');
    item.className = 'stree-item';

    const row = document.createElement('div');
    row.className = 'stree-row';
    row.dataset.cat = child.path;
    row.style.paddingLeft = (8 + depth * 14) + 'px';

    const indicator = document.createElement('span');
    indicator.className = 'stree-toggle';
    indicator.style.pointerEvents = 'none';
    indicator.textContent = hasChildren ? '▶' : '';
    row.appendChild(indicator);

    const nameSpan = document.createElement('span');
    nameSpan.className = 'stree-name';
    nameSpan.textContent = dirName;
    row.appendChild(nameSpan);

    row.style.cursor = 'pointer';
    row.addEventListener('click', e => {
      if (e.target.closest('.stree-folder-actions')) return;
      setCat(child.path, row);
      if (hasChildren) {
        const exp = item.classList.toggle('expanded');
        indicator.textContent = exp ? '▼' : '▶';
      }
    });

    addFolderDrop(row, child.path);
    item.appendChild(row);

    if (hasChildren) {
      const children = document.createElement('div');
      children.className = 'stree-children';
      renderSidebarNode(child, children, depth + 1);
      item.appendChild(children);
    }

    container.appendChild(item);
  });
}

function makeFlatBtn(cat, label, count) {
  const btn = document.createElement('button');
  btn.className = 'cat-btn';
  btn.dataset.cat = cat;
  btn.innerHTML =
    `<div class="cat-accent"></div>` +
    `<div class="cat-inner">` +
    `<span class="cat-label">${esc(label)}</span>` +
    `<span class="cat-badge">${count}</span>` +
    `</div>`;
  btn.addEventListener('click', () => setCat(cat, btn));
  return btn;
}

function setCat(cat, el) {
  activeCat = cat === '' ? null : cat;
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.stree-row').forEach(r => {
    r.classList.remove('active');
    r.querySelectorAll('.stree-folder-actions').forEach(a => a.remove());
  });
  const ic = document.getElementById('fm-inline-create');
  if (ic) ic.remove();
  if (el) {
    el.classList.add('active');
    if (activeCat && activeCat !== '__fav__' && activeCat !== '__recent__') addFolderActions(el, activeCat);
  }
  applyFilter();
  document.getElementById('content').scrollTo({ top: 0, behavior: 'smooth' });
}

/* ── フィルタ ── */
function onSearch() { applyFilter(); }

function applyFilter() {
  const q = document.getElementById('search').value.toLowerCase();
  const favs = getFavs();
  const recent = getRecent();
  let total = 0;
  document.querySelectorAll('.card').forEach(card => {
    const lora = JSON.parse(card.dataset.lora);
    const cat = lora.category || '';
    const catMatch = activeCat === null || activeCat === '__fav__' || activeCat === '__recent__' ||
      cat === activeCat || (activeCat !== '' && cat.startsWith(activeCat + '/'));
    const favMatch = activeCat !== '__fav__' || favs.includes(lora.name);
    const recentMatch = activeCat !== '__recent__' || recent.includes(lora.name);
    const textMatch = !q
      || lora.name.toLowerCase().includes(q)
      || lora.model_name.toLowerCase().includes(q)
      || (lora.activation_text || '').toLowerCase().includes(q)
      || (lora.tags || []).some(t => t.toLowerCase().includes(q));
    const show = catMatch && favMatch && recentMatch && textMatch;
    card.style.display = show ? '' : 'none';
    if (show) total++;
  });
  updateCount(total);
}

function updateCount(n) {
  const el = document.getElementById('count');
  if (!el) return;
  const shown = n !== undefined ? n : allLoras.length;
  el.textContent = shown + ' / ' + allLoras.length;
}

/* ── カード生成 ── */
function makeCard(lora) {
  const card = document.createElement('div');
  card.className = 'card' + (isFav(lora.name) ? ' fav-card' : '');
  card.dataset.lora = JSON.stringify(lora);

  const imgHtml = lora.preview
    ? `<img class="card-img" src="/lora_browser/preview?path=${encodeURIComponent(lora.preview)}&w=420&_v=${previewVer}"
         loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
    : '';
  const placeholderStyle = lora.preview ? 'display:none' : '';
  card.innerHTML =
    imgHtml +
    `<div class="card-placeholder" style="${placeholderStyle}">🖼️</div>` +
    `<div class="card-top">` +
    (lora.base_model ? `<span class="card-base-badge">${esc(abbrevModel(lora.base_model))}</span>` : '<span></span>') +
    `<div class="card-action-btns">` +
    `<button class="card-fav-btn ${isFav(lora.name) ? 'active' : ''}"
       onclick="onCardFav(event,this,'${esc(lora.name)}')">${isFav(lora.name) ? '★' : '☆'}</button>` +
    `</div>` +
    `</div>` +
    `<div class="card-bottom">` +
    `<div class="card-name">${esc(lora.model_name)}</div>` +
    `</div>`;

  card.addEventListener('click', () => openModal(lora));
  card.draggable = true;
  card.addEventListener('dragstart', e => {
    e.dataTransfer.setData('text/lora-name', lora.name);
    e.dataTransfer.effectAllowed = 'move';
    card.classList.add('dragging');
  });
  card.addEventListener('dragend', () => card.classList.remove('dragging'));
  return card;
}

function onCardSendTxt(e, btn) {
  e.stopPropagation();
  const lora = JSON.parse(btn.closest('.card').dataset.lora);
  const text = '<lora:' + lora.name + ':' + currentWeight + '>';
  navigator.clipboard.writeText(text).catch(() => {});
  tryInsert(text);
  showToast('Sent: ' + text);
}

function onCardCivitai(e, modelId, versionId) {
  e.stopPropagation();
  window.open('https://civitai.com/models/' + modelId +
    (versionId ? '?modelVersionId=' + versionId : ''), '_blank');
}

function onCardOpenFolder(e, name) {
  e.stopPropagation();
  fetch('/lora_browser/open_folder?name=' + encodeURIComponent(name));
}

function onCardFav(e, btn, name) {
  e.stopPropagation();
  const nowFav = toggleFav(name);
  btn.textContent = nowFav ? '★' : '☆';
  btn.classList.toggle('active', nowFav);
  btn.closest('.card').classList.toggle('fav-card', nowFav);
  updateFavSidebarCount();
  if (activeCat === '__fav__') applyFilter();
}

/* ── モーダル ── */
function openModal(lora) {
  currentLora = lora;
  activeWords.clear();
  activeSampleSends.clear();
  sentLoraText = null;

  document.getElementById('modal-model-name').innerHTML =
    `<span>${esc(lora.model_name)}</span>` +
    `<button class="icon-action-btn" onclick="startRename()" title="Rename display name" style="flex-shrink:0">${SVG_PENCIL}</button>`;

  const civBtn = document.getElementById('btn-civitai');
  if (lora.civitai_model_id) {
    civBtn.style.display = '';
    civBtn.dataset.modelId = lora.civitai_model_id;
    civBtn.dataset.versionId = lora.civitai_version_id || '';
  } else {
    civBtn.style.display = 'none';
  }

  const previewCol = document.getElementById('modal-preview-col');
  const imgPart = lora.preview
    ? `<div id="preview-img-wrap">` +
      `<img id="modal-preview-img" src="/lora_browser/preview?path=${encodeURIComponent(lora.preview)}&w=400&_v=${previewVer}" onerror="this.style.display='none'">` +
      `<div id="preview-change-overlay" onclick="triggerPreviewUpload()"><span>📷 Change</span></div>` +
      `</div>`
    : `<div id="preview-img-wrap" style="min-height:80px;display:flex;align-items:center;justify-content:center">` +
      `<div class="placeholder">🖼️</div>` +
      `<div id="preview-change-overlay" onclick="triggerPreviewUpload()"><span>📷 Set Image</span></div>` +
      `</div>`;
  previewCol.innerHTML = imgPart +
    `<input type="file" id="preview-file-input" accept="image/*" style="display:none" onchange="onPreviewFileSelected(this)">` +
    `<div id="modal-preview-info">` +
    `<div class="pvi-item">` +
    `<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">` +
    `<div class="pvi-label">Tags</div>` +
    `<button class="icon-action-btn" onclick="startEditTags()" title="Edit tags">${SVG_PENCIL}</button>` +
    `</div>` +
    `<div id="pvi-tags-view">${renderTagsReadonly(lora.tags)}</div>` +
    `</div>` +
    `</div>`;

  const trainedWordsHtml =
    `<div class="info-section">` +
    `<div class="tw-header">` +
    `<div class="info-label">Trigger Words<span class="info-label-hint">Click to add to txt2img</span></div>` +

    `<button class="icon-action-btn" onclick="toggleEditWords()" title="Edit trigger words">${SVG_PENCIL}</button>` +
    `</div>` +
    `<div id="tw-container"></div>` +
    `</div>`;

  document.getElementById('modal-info-col').innerHTML =
    `<div class="info-section">` +
    `<div class="info-label">Syntax</div>` +
    `<div class="lora-syntax-row">` +
    `<div class="lora-syntax-box" id="lora-syntax-display"></div>` +
    `<input id="modal-weight" class="lora-weight-input" type="number" value="${currentWeight}" min="0" max="2" step="0.05" oninput="updateSyntax()" title="Weight">` +
    `<button id="lora-send-btn" class="lora-send-btn" onclick="sendTo()" title="Send to txt2img">➤</button>` +
    `</div>` +
    `</div>` +
    trainedWordsHtml +
    `<div class="info-section">` +
    (lora.base_model ?
      `<div class="info-label">Model</div>` +
      `<div class="pvi-value" style="margin-bottom:12px;font-size:14px">${esc(lora.base_model)}</div>` : '') +
    `<div class="info-label" style="margin-bottom:4px">File Name</div>` +
    `<div id="filename-view" style="display:flex;align-items:center;gap:6px;margin-bottom:8px">` +
    `<div style="flex:1;font-size:14px;color:var(--txt3);word-break:break-all;line-height:1.4">${esc(lora.name)}.safetensors</div>` +
    `<button class="icon-action-btn" onclick="startFileRename()" title="Rename file">${SVG_PENCIL}</button></div>` +
    `<div id="filename-edit" style="display:none;margin-bottom:10px">` +
    `<input id="filename-input" style="width:100%;background:var(--bg3);border:1px solid var(--pri);border-radius:6px;color:var(--txt);font-size:13px;padding:5px 8px" value="${esc(lora.name)}">` +
    `<div style="display:flex;gap:4px;margin-top:4px">` +
    `<button class="tw-edit-btn" style="flex:1" onclick="saveFileRename()">Save</button>` +
    `<button class="tw-edit-btn" onclick="cancelFileRename()">Cancel</button></div></div>` +
    (lora.file_path ?
      `<div class="info-label" style="margin-bottom:4px">Path</div>` +
      `<div style="display:flex;align-items:flex-start;gap:6px">` +
      `<div style="flex:1;font-size:14px;color:var(--txt3);word-break:break-all;line-height:1.4">${esc(lora.file_path)}</div>` +
      `<button class="icon-action-btn" onclick="openFolderModal()" title="Open folder">${SVG_FOLDER}</button></div>` : '') +
    `</div>` +
    buildSampleImages(lora.sample_images) +
    (lora.civitai_html ?
      `<div class="info-section">` +
      `<div class="tw-header"><div class="info-label">Description</div>` +
      `<button class="tw-edit-btn" onclick="toggleSection(this)">Show</button></div>` +
      `<div class="civitai-html-wrap" style="display:none">${lora.civitai_html}</div>` +
      `</div>` : '');

  updateSyntax();
  showTrainedWords(lora.trained_words || []);

  document.getElementById('modal-overlay').style.display = 'flex';
  document.addEventListener('keydown', onModalKey);
}

function closeModal() {
  document.getElementById('modal-overlay').style.display = 'none';
  document.removeEventListener('keydown', onModalKey);
  currentLora = null;
  sentLoraText = null;
}
function onOverlayClick(e) {
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}
function onModalKey(e) { if (e.key === 'Escape') closeModal(); }

function startRename() {
  if (!currentLora) return;
  const nameEl = document.getElementById('modal-model-name');
  const cur = currentLora.model_name;
  nameEl.innerHTML =
    `<input id="rename-input" style="flex:1;background:var(--bg3);border:1px solid var(--pri);` +
    `border-radius:6px;color:var(--txt);font-size:inherit;font-weight:inherit;padding:2px 8px;width:100%;" value="${esc(cur)}">` +
    `<span style="display:flex;gap:6px;margin-top:6px;">` +
    `<button class="tw-edit-btn" onclick="saveRename()">Save</button>` +
    `<button class="tw-edit-btn" onclick="cancelRename()">Cancel</button></span>`;
  const inp = document.getElementById('rename-input');
  inp.focus(); inp.select();
  inp.addEventListener('keydown', e => { if (e.key==='Enter') saveRename(); if (e.key==='Escape') cancelRename(); });
}
function cancelRename() {
  if (!currentLora) return;
  document.getElementById('modal-model-name').innerHTML =
    `<span>${esc(currentLora.model_name)}</span>` +
    `<button class="icon-action-btn" onclick="startRename()" title="Rename display name" style="flex-shrink:0">${SVG_PENCIL}</button>`;
}
async function saveRename() {
  if (!currentLora) return;
  const inp = document.getElementById('rename-input');
  if (!inp) return;
  const newName = inp.value.trim();
  if (!newName) return;
  try {
    const res = await fetch('/lora_browser/rename', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: currentLora.name, model_name: newName})
    });
    if (!res.ok) throw new Error((await res.json()).error || 'Rename failed');
    currentLora.model_name = newName;
    document.getElementById('modal-model-name').innerHTML =
      `<span>${esc(newName)}</span>` +
      `<button class="icon-action-btn" onclick="startRename()" title="Rename display name" style="flex-shrink:0">${SVG_PENCIL}</button>`;
    allLoras.forEach(l => { if (l.name === currentLora.name) l.model_name = newName; });
    document.querySelectorAll('.card').forEach(card => {
      try {
        const d = JSON.parse(card.dataset.lora);
        if (d.name === currentLora.name) {
          d.model_name = newName;
          card.dataset.lora = JSON.stringify(d);
          const el = card.querySelector('.card-name');
          if (el) el.textContent = newName;
        }
      } catch(e) {}
    });
    showToast('Renamed');
  } catch(e) { showToast('Error: ' + e.message); cancelRename(); }
}

/* ── プロンプト送信 ── */
function updateSyntax() {
  const inp = document.getElementById('modal-weight');
  if (inp) {
    const newW = parseFloat(inp.value) || 1.0;
    if (newW !== currentWeight && sentLoraText !== null) {
      const btn = document.getElementById('lora-send-btn');
      if (btn) { btn.classList.remove('sent'); btn.innerHTML = SEND_ICON; btn.title = 'Send to txt2img'; }
      sentLoraText = null;
    }
    currentWeight = newW;
  }
  if (!currentLora) return;
  const el = document.getElementById('lora-syntax-display');
  if (el) el.textContent = '<lora:' + currentLora.name + ':' + currentWeight + '>';
}

const SEND_ICON = '➤';
const UNDO_ICON = '✕';
const SVG_ADD = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;
const SVG_SENT = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`;
const SVG_INJECT = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="13 6 19 12 13 18"/></svg>`;
const SVG_PENCIL = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>`;
const SVG_FOLDER = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`;

function sendTo() {
  if (!currentLora) return;
  const btn = document.getElementById('lora-send-btn');
  if (sentLoraText !== null) {
    removeWordFromPrompt(sentLoraText, sentLoraText);
    sentLoraText = null;
    if (btn) { btn.classList.remove('sent'); btn.innerHTML = SEND_ICON; btn.title = 'Send to txt2img'; }
    showToast('Removed');
  } else {
    const text = '<lora:' + currentLora.name + ':' + currentWeight + '>';
    navigator.clipboard.writeText(text).catch(() => {});
    sentLoraText = insertWordToPrompt(text, false);
    addRecent(currentLora.name);
    if (btn) { btn.classList.add('sent'); btn.innerHTML = UNDO_ICON; btn.title = 'Undo'; }
    showToast('Sent: ' + text);
  }
}

function showTrainedWords(words) {
  const container = document.getElementById('tw-container');
  if (!container) return;
  if (!words || !words.length) {
    container.innerHTML = '<div style="color:#4b5563;font-size:12px">No trigger words</div>';
    return;
  }
  container.innerHTML =
    `<div class="trained-words-wrap">` +
    words.map(tw =>
      `<div class="trained-word-item" data-word="${esc(tw)}" onclick="sendTrainedWord(this)">` +
      `<span class="trained-word-text">${esc(tw)}</span>` +
      `<span class="trained-word-send">+</span>` +
      `</div>`
    ).join('') +
    `</div>`;
}

function buildEditWordItem(w) {
  const div = document.createElement('div');
  div.className = 'trained-word-item';
  div.style.cursor = 'default';
  div.innerHTML =
    `<span class="trained-word-text" style="cursor:text;flex:1" title="Click to edit" onclick="inlineEditWord(this)">${esc(w)}</span>` +
    `<button class="tw-del-btn" onclick="this.closest('.trained-word-item').remove()" title="Remove" style="font-size:16px">×</button>`;
  return div;
}
function inlineEditWord(span) {
  const val = span.textContent;
  const inp = document.createElement('textarea');
  inp.className = 'trained-word-text';
  inp.style.cssText = 'flex:1;background:var(--bg3);border:1px solid var(--pri);border-radius:4px;color:var(--txt);font-size:13px;padding:2px 6px;outline:none;resize:none;overflow:hidden;line-height:1.5;word-break:break-all;';
  inp.value = val;
  inp.rows = 1;
  span.replaceWith(inp);
  inp.style.height = 'auto';
  inp.style.height = inp.scrollHeight + 'px';
  inp.addEventListener('input', () => { inp.style.height = 'auto'; inp.style.height = inp.scrollHeight + 'px'; });
  inp.focus(); inp.select();
  const done = () => {
    const s = document.createElement('span');
    s.className = 'trained-word-text';
    s.style.cssText = 'cursor:text;flex:1';
    s.title = 'Click to edit';
    s.textContent = inp.value.trim() || val;
    s.onclick = function() { inlineEditWord(this); };
    inp.replaceWith(s);
  };
  inp.addEventListener('blur', done);
  inp.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); inp.blur(); } });
}
function addWordFromInput() {
  const inp = document.getElementById('tw-new-word');
  if (!inp) return;
  const w = inp.value.trim();
  if (!w) return;
  const list = document.getElementById('tw-edit-list');
  if (list) list.appendChild(buildEditWordItem(w));
  inp.value = ''; inp.focus();
}
function toggleEditWords() {
  const container = document.getElementById('tw-container');
  if (container && container.querySelector('#tw-edit-list')) {
    cancelEditWords();
  } else {
    startEditWords();
  }
}
function startEditWords() {
  if (!currentLora) return;
  const container = document.getElementById('tw-container');
  if (!container) return;
  const words = currentLora.trained_words || [];
  const wrap = document.createElement('div');
  const list = document.createElement('div');
  list.id = 'tw-edit-list';
  list.className = 'trained-words-wrap';
  words.forEach(w => list.appendChild(buildEditWordItem(w)));
  const addRow = document.createElement('div');
  addRow.className = 'tw-edit-row';
  addRow.style.marginTop = '8px';
  addRow.innerHTML =
    `<textarea id="tw-new-word" class="tw-edit-input" placeholder="Add trigger word..." rows="1" ` +
    `style="resize:none;overflow:hidden;line-height:1.5;word-break:break-all;" ` +
    `onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();addWordFromInput()}" ` +
    `oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px'"></textarea>` +
    `<button class="tw-add-btn" style="width:auto;padding:0 12px;margin:0;border-style:solid;font-size:18px" onclick="addWordFromInput()">+</button>`;
  const actions = document.createElement('div');
  actions.className = 'tw-edit-actions';
  actions.innerHTML =
    `<button class="tw-save-btn" onclick="saveWords()">Save</button>` +
    `<button class="tw-cancel-btn" onclick="cancelEditWords()">Cancel</button>`;
  wrap.appendChild(list);
  wrap.appendChild(addRow);
  wrap.appendChild(actions);
  container.innerHTML = '';
  container.appendChild(wrap);
}

async function saveWords() {
  if (!currentLora) return;
  const container = document.getElementById('tw-container');
  if (!container) return;
  const words = Array.from(container.querySelectorAll('#tw-edit-list .trained-word-item'))
    .map(item => {
      const inp = item.querySelector('input, textarea');
      const span = item.querySelector('.trained-word-text');
      return (inp ? inp.value : (span ? span.textContent : '')).trim();
    })
    .filter(w => w);
  try {
    const res = await fetch('/lora_browser/save_trigger_words', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: currentLora.name, words })
    });
    if (!res.ok) throw new Error('Save failed');
    currentLora.trained_words = words;
    allLoras.forEach(l => { if (l.name === currentLora.name) l.trained_words = words; });
    document.querySelectorAll('.card').forEach(card => {
      const lora = JSON.parse(card.dataset.lora);
      if (lora.name === currentLora.name) {
        lora.trained_words = words;
        card.dataset.lora = JSON.stringify(lora);
      }
    });
    showTrainedWords(words);
    showToast('Saved');
  } catch(e) {
    showToast('Error: ' + e.message);
  }
}

function cancelEditWords() {
  if (!currentLora) return;
  showTrainedWords(currentLora.trained_words || []);
}

function sendTrainedWord(el) {
  const word = el.dataset.word;
  const sendEl = el.querySelector('.trained-word-send');
  if (activeWords.has(word)) {
    removeWordFromPrompt(word, activeWords.get(word));
    activeWords.delete(word);
    el.classList.remove('tw-active');
    if (sendEl) sendEl.textContent = '+';
    showToast('Removed');
  } else {
    const inserted = insertWordToPrompt(word);
    activeWords.set(word, inserted);
    el.classList.add('tw-active');
    if (sendEl) sendEl.textContent = '−';
    showToast('Added: ' + (word.length > 50 ? word.slice(0, 50) + '…' : word));
  }
}

function insertWordToPrompt(word, addComma = true) {
  const cleanWord = word.replace(/,\s*$/, '').trim();
  const fallback = cleanWord + (addComma ? ',' : '');
  try {
    const w = getHostWindow();
    if (!w) return fallback;
    const ta = w.document.querySelector('#txt2img_prompt textarea');
    if (!ta) return fallback;
    const pos = ta.selectionStart;
    const selEnd = ta.selectionEnd;
    const v = ta.value;
    const before = v.slice(0, pos);
    const after = v.slice(selEnd);
    // Use trimmed only for separator decision — don't strip newlines from actual text
    const lastNonWS = before.replace(/[^\S\n]+$/, '');   // strip trailing spaces/tabs only
    const firstNonWS = after.replace(/^[^\S\n]+/, '');   // strip leading spaces/tabs only
    const atLineStart = lastNonWS.endsWith('\n');
    const sepBefore = !lastNonWS || atLineStart ? '' : lastNonWS.endsWith(',') ? ' ' : ', ';
    const commaAfter = addComma ? (firstNonWS && !firstNonWS.startsWith(',') ? ', ' : ',') : '';
    const toInsert = sepBefore + cleanWord + commaAfter;
    const newVal = before + toInsert + after;
    ta.value = newVal;
    ta.selectionStart = ta.selectionEnd = before.length + toInsert.length;
    ta.dispatchEvent(new Event('input', { bubbles: true }));
    return toInsert;
  } catch(e) { return fallback; }
}

function removeWordFromPrompt(word, inserted) {
  try {
    const w = getHostWindow();
    if (!w) return;
    const ta = w.document.querySelector('#txt2img_prompt textarea');
    if (!ta) return;
    let v = ta.value;
    const idx = v.lastIndexOf(inserted);
    if (idx !== -1) {
      v = v.slice(0, idx) + v.slice(idx + inserted.length);
    } else {
      // Strip leading/trailing separators to get bare word (handles case where word === inserted)
      const cleanWord = (inserted || word).replace(/^[\s,]+/, '').replace(/[\s,]+$/, '').trim();
      const escaped = cleanWord.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      v = v.replace(new RegExp(',\\s*' + escaped, ''), '')
           .replace(new RegExp(escaped + '\\s*,\\s*', ''), '')
           .replace(new RegExp(escaped, ''), '');
    }
    ta.value = v.trim().replace(/^,\s*/, '').replace(/,\s*$/, '');
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  } catch(e) {}
}

async function deleteLora() {
  if (!currentLora) return;
  if (!confirm('Delete "' + currentLora.model_name + '"?\nThis cannot be undone.')) return;
  try {
    const res = await fetch('/lora_browser/delete?name=' + encodeURIComponent(currentLora.name), { method: 'DELETE' });
    if (!res.ok) throw new Error((await res.json()).error || 'Delete failed');
    const name = currentLora.name;
    const modelName = currentLora.model_name;
    allLoras = allLoras.filter(l => l.name !== name);
    document.querySelectorAll('.card').forEach(card => {
      if (JSON.parse(card.dataset.lora).name === name) {
        const block = card.closest('.section-block');
        card.remove();
        if (block && !block.querySelector('.card')) block.remove();
      }
    });
    updateCount(allLoras.length);
    closeModal();
    showToast('Deleted: ' + modelName);
  } catch(e) {
    showToast('Error: ' + e.message);
  }
}

function triggerPreviewUpload() {
  const inp = document.getElementById('preview-file-input');
  if (inp) inp.click();
}
async function onPreviewFileSelected(input) {
  const file = input.files[0];
  if (!file || !currentLora) return;
  input.value = '';
  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64 = e.target.result.split(',')[1];
    const ext = file.name.split('.').pop().toLowerCase();
    try {
      const res = await fetch('/lora_browser/set_preview', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: currentLora.name, image: base64, ext})
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed');
      const img = document.getElementById('modal-preview-img');
      if (img) { img.src = e.target.result; img.style.display = ''; }
      else {
        const wrap = document.getElementById('preview-img-wrap');
        if (wrap) wrap.innerHTML =
          `<img id="modal-preview-img" src="${e.target.result}" style="width:100%;object-fit:cover;object-position:center top">` +
          `<div id="preview-change-overlay" onclick="triggerPreviewUpload()"><span>📷 Change</span></div>`;
      }
      showToast('Preview updated');
    } catch(e) { showToast('Error: ' + e.message); }
  };
  reader.readAsDataURL(file);
}
function openCivitai() {
  const btn = document.getElementById('btn-civitai');
  const modelId = btn.dataset.modelId;
  const versionId = btn.dataset.versionId;
  if (!modelId) return;
  window.open('https://civitai.com/models/' + modelId +
    (versionId ? '?modelVersionId=' + versionId : ''), '_blank');
}

async function fetchCivitai() {
  if (!currentLora) return;
  const btn = document.getElementById('btn-fetch-civitai');
  btn.disabled = true;
  btn.textContent = '⏳ Fetching...';
  try {
    const res = await fetch('/lora_browser/fetch_civitai', {
      method: 'POST',
      headers: getCivitaiHeaders(),
      body: JSON.stringify({name: currentLora.name, force: true, dl_preview: true})
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      showToast('Error: ' + (data.error || 'Unknown'));
      return;
    }
    showToast('Fetched: ' + (data.model_name || currentLora.name));
    await loadLoras();
    const updated = allLoras.find(l => l.name === currentLora.name);
    if (updated) openModal(updated);
  } catch(e) {
    showToast('Error: ' + e.message);
  } finally {
    btn.disabled = false;
    if (btn.textContent === '⏳ Fetching...') btn.textContent = '🔄 Fetch';
  }
}

let bulkFetchRunning = false;
let bulkFetchAbort = false;

async function startBulkFetch() {
  if (bulkFetchRunning) return;
  bulkFetchRunning = true;
  bulkFetchAbort = false;
  const progress = document.getElementById('bulk-fetch-progress');
  const startBtn = document.getElementById('bulk-fetch-start-btn');
  progress.style.display = 'flex';
  if (startBtn) startBtn.disabled = true;
  document.getElementById('bulk-fetch-stop-btn').style.display = '';
  document.getElementById('bulk-fetch-result').textContent = '';
  document.getElementById('bulk-fetch-bar').style.width = '0';
  try {
    document.getElementById('bulk-fetch-status').textContent = 'Loading LoRA list...';
    const res = await fetch('/lora_browser/civitai_missing');
    const data = await res.json();
    const missing = (data.loras || []).filter(l => !l.has_meta);
    const total = missing.length;
    if (total === 0) {
      document.getElementById('bulk-fetch-status').textContent = 'All LoRAs already have metadata';
      document.getElementById('bulk-fetch-result').textContent = 'Nothing to fetch';
      return;
    }
    let done = 0, found = 0, notFound = 0;
    for (const lora of missing) {
      if (bulkFetchAbort) break;
      document.getElementById('bulk-fetch-status').textContent = lora.name;
      try {
        const r = await fetch('/lora_browser/fetch_civitai', {
          method: 'POST',
          headers: getCivitaiHeaders(),
          body: JSON.stringify({name: lora.name, force: false, dl_preview: true})
        });
        const d = await r.json();
        if (d.ok && !d.skipped) found++;
        else if (!d.ok) notFound++;
      } catch(e) { notFound++; }
      done++;
      document.getElementById('bulk-fetch-bar').style.width = (done / total * 100) + '%';
      document.getElementById('bulk-fetch-result').textContent =
        done + ' / ' + total + ' processed (fetched: ' + found + '  not found: ' + notFound + ')';
    }
    document.getElementById('bulk-fetch-status').textContent = bulkFetchAbort ? 'Stopped' : 'Done';
    await loadLoras();
  } catch(e) {
    document.getElementById('bulk-fetch-status').textContent = 'Error: ' + e.message;
  } finally {
    bulkFetchRunning = false;
    document.getElementById('bulk-fetch-stop-btn').style.display = 'none';
    if (startBtn) startBtn.disabled = false;
  }
}

async function openSettings() {
  document.getElementById('settings-civitai-key').value = getSetting('civitai_api_key', '');
  document.getElementById('settings-show-favs').checked = getSetting('show_favs', '1') === '1';
  document.getElementById('settings-show-recent').checked = getSetting('show_recent', '1') === '1';
  document.getElementById('bulk-fetch-progress').style.display = 'none';
  try {
    const res = await fetch('/lora_browser/config');
    const cfg = await res.json();
    document.getElementById('settings-lora-dir').value = cfg.lora_dir || '';
  } catch(e) {}
  document.getElementById('settings-overlay').style.display = 'flex';
}
function closeSettings() {
  if (bulkFetchRunning) return;
  document.getElementById('settings-overlay').style.display = 'none';
}
function _saveSettingsLocal() {
  setSetting('civitai_api_key', document.getElementById('settings-civitai-key').value.trim());
  setSetting('show_favs', document.getElementById('settings-show-favs').checked ? '1' : '0');
  setSetting('show_recent', document.getElementById('settings-show-recent').checked ? '1' : '0');
}
async function saveSettings() {
  _saveSettingsLocal();
  const loraDir = document.getElementById('settings-lora-dir').value.trim();
  await fetch('/lora_browser/config', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({lora_dir: loraDir})
  });
  rebuildSidebar();
  closeSettings();
  showToast('Settings saved');
}
async function saveSettingsOnly() {
  _saveSettingsLocal();
  const loraDir = document.getElementById('settings-lora-dir').value.trim();
  await fetch('/lora_browser/config', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({lora_dir: loraDir})
  });
}
function onSettingsOverlayClick(e) {
  if (e.target === document.getElementById('settings-overlay')) closeSettings();
}
function getCivitaiHeaders() {
  const key = getSetting('civitai_api_key', '');
  return key ? {'Content-Type': 'application/json', 'X-Civitai-Api-Key': key}
             : {'Content-Type': 'application/json'};
}

function getHostWindow() {
  if (window.opener && !window.opener.closed) return window.opener;
  if (window.parent && window.parent !== window) return window.parent;
  return null;
}

function tryInsert(text) {
  try {
    const w = getHostWindow();
    if (!w) return;
    const ta = w.document.querySelector('#txt2img_prompt textarea');
    if (!ta) return;
    const s = ta.selectionStart, e2 = ta.selectionEnd, v = ta.value;
    const sep = (v && !v.endsWith(' ') && s === v.length) ? ' ' : '';
    ta.value = v.slice(0, s) + sep + text + v.slice(e2);
    ta.selectionStart = ta.selectionEnd = s + sep.length + text.length;
    ta.dispatchEvent(new Event('input', { bubbles: true }));
    ta.focus();
  } catch(e) {}
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2400);
}

/* ── Recently Used (localStorage) ── */
const RECENT_MAX = 20;
function getRecent() {
  try { return JSON.parse(localStorage.getItem('lora_recent') || '[]'); } catch { return []; }
}
function addRecent(name) {
  let recent = getRecent().filter(n => n !== name);
  recent.unshift(name);
  if (recent.length > RECENT_MAX) recent = recent.slice(0, RECENT_MAX);
  localStorage.setItem('lora_recent', JSON.stringify(recent));
  updateRecentSidebarCount();
}
function updateRecentSidebarCount() {
  const btn = document.getElementById('recent-sidebar-btn');
  if (btn) btn.querySelector('.cat-badge').textContent = getRecent().length;
  if (activeCat === '__recent__') applyFilter();
}

/* ── お気に入り (localStorage) ── */
function getFavs() {
  try { return JSON.parse(localStorage.getItem('lora_favs') || '[]'); } catch { return []; }
}
function isFav(name) { return getFavs().includes(name); }
function toggleFav(name) {
  let favs = getFavs();
  if (favs.includes(name)) favs = favs.filter(f => f !== name);
  else favs.push(name);
  localStorage.setItem('lora_favs', JSON.stringify(favs));
  return favs.includes(name);
}
function updateFavSidebarCount() {
  const btn = document.getElementById('fav-sidebar-btn');
  if (btn) btn.querySelector('.cat-badge').textContent = getFavs().length;
  // お気に入りフィルタ中なら再フィルタして件数更新
  if (activeCat === '__fav__') applyFilter();
}

/* ── ユーティリティ ── */
function groupByCategory(loras) {
  const g = {};
  loras.forEach(l => { const k = l.category || ''; if (!g[k]) g[k] = []; g[k].push(l); });
  return g;
}
function sortedCats(groups) {
  return Object.keys(groups).sort((a, b) => {
    if (!a && b) return -1; if (a && !b) return 1;
    return a.localeCompare(b, 'ja');
  });
}
function esc(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function startFileRename() {
  document.getElementById('filename-view').style.display = 'none';
  document.getElementById('filename-edit').style.display = '';
  const inp = document.getElementById('filename-input');
  if (inp && currentLora) { inp.value = currentLora.name; inp.focus(); inp.select(); }
  inp && inp.addEventListener('keydown', e => { if (e.key==='Enter') saveFileRename(); if (e.key==='Escape') cancelFileRename(); });
}
function cancelFileRename() {
  document.getElementById('filename-edit').style.display = 'none';
  document.getElementById('filename-view').style.display = 'flex';
}
async function saveFileRename() {
  if (!currentLora) return;
  const inp = document.getElementById('filename-input');
  if (!inp) return;
  const newName = inp.value.trim();
  if (!newName || newName === currentLora.name) { cancelFileRename(); return; }
  try {
    const res = await fetch('/lora_browser/rename_file', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: currentLora.name, new_name: newName})
    });
    if (!res.ok) throw new Error((await res.json()).error || 'Failed');
    showToast('File renamed — reloading...');
    closeModal();
    loadLoras();
  } catch(e) { showToast('Error: ' + e.message); cancelFileRename(); }
}
let tagsDraft = [];
function renderTagsReadonly(tags) {
  if (!tags || !tags.length) return `<span class="pvi-value" style="color:var(--txt5)">None</span>`;
  return `<div class="pvi-tags">` + tags.map(t => `<span class="pvi-tag">${esc(t)}</span>`).join('') + `</div>`;
}
function renderTagsEditOverlay() {
  const list = document.getElementById('tags-edit-list');
  if (!list) return;
  if (!tagsDraft.length) {
    list.innerHTML = `<span style="color:var(--txt5);font-size:12px">No tags yet</span>`;
    return;
  }
  list.innerHTML = tagsDraft.map(t =>
    `<span class="pvi-tag" style="display:inline-flex;align-items:center;gap:3px;font-size:12px;padding:3px 8px">` +
    `${esc(t)}<button data-tag="${esc(t)}" onclick="removeTagDraft(this.dataset.tag)" ` +
    `style="background:none;border:none;color:var(--txt4);cursor:pointer;font-size:13px;padding:0 0 0 4px;line-height:1">×</button>` +
    `</span>`
  ).join('');
}
function startEditTags() {
  if (!currentLora) return;
  tagsDraft = [...(currentLora.tags || [])];
  renderTagsEditOverlay();
  document.getElementById('tags-edit-overlay').style.display = 'flex';
  const inp = document.getElementById('tags-edit-input');
  if (inp) { inp.value = ''; inp.focus(); }
}
function cancelEditTags() {
  document.getElementById('tags-edit-overlay').style.display = 'none';
}
function onTagsOverlayClick(e) {
  if (e.target === document.getElementById('tags-edit-overlay')) cancelEditTags();
}
function removeTagDraft(tag) {
  tagsDraft = tagsDraft.filter(t => t !== tag);
  renderTagsEditOverlay();
}
function addTagDraft() {
  const inp = document.getElementById('tags-edit-input');
  if (!inp) return;
  const newTag = inp.value.trim();
  if (!newTag) return;
  if (!tagsDraft.includes(newTag)) {
    tagsDraft.push(newTag);
    renderTagsEditOverlay();
  }
  inp.value = '';
  inp.focus();
}
async function saveTagsEdit() {
  await saveTags(tagsDraft);
  document.getElementById('tags-edit-overlay').style.display = 'none';
}
async function saveTags(tags) {
  if (!currentLora) return;
  try {
    const res = await fetch('/lora_browser/save_tags', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: currentLora.name, tags})
    });
    if (!res.ok) throw new Error('Save failed');
    currentLora.tags = tags;
    allLoras.forEach(l => { if (l.name === currentLora.name) l.tags = tags; });
    const view = document.getElementById('pvi-tags-view');
    if (view) view.innerHTML = renderTagsReadonly(tags);
    showToast('Tags saved');
  } catch(e) { showToast('Error: ' + e.message); }
}
function toggleSection(btn) {
  const content = btn.parentElement.nextElementSibling;
  const visible = content.style.display !== 'none';
  content.style.display = visible ? 'none' : '';
  btn.textContent = visible ? 'Show' : 'Hide';
}
function openFolderModal() {
  if (!currentLora) return;
  fetch('/lora_browser/open_folder?name=' + encodeURIComponent(currentLora.name));
}
function buildSampleImages(images) {
  if (!images || !images.length) return '';
  const cards = images.map((img, idx) => {
    const chips = [];
    if (img.size)    chips.push(['SIZE', esc(img.size)]);
    if (img.sampler) chips.push(['SAMPLER', esc(img.sampler)]);
    if (img.steps)   chips.push(['STEPS', esc(String(img.steps))]);
    if (img.cfg)     chips.push(['CFG', esc(String(img.cfg))]);
    if (img.seed)    chips.push(['SEED', esc(String(img.seed))]);
    const chipsHtml = chips.map(([l,v]) =>
      `<span class="si-chip"><span class="si-chip-label">${l}</span><span class="si-chip-val">${v}</span></span>`
    ).join('');
    return `<div class="si-card">` +
      `<div class="si-img-wrap">` +
      `<img class="si-img" src="${esc(img.url)}" loading="lazy" onerror="this.closest('.si-card').style.display='none'">` +
      `</div>` +
      (chipsHtml || img.model ? `<div class="si-meta-bar">` +
        (chipsHtml ? `<div class="si-meta-chips">${chipsHtml}</div>` : '') +
        (img.model ? `<div class="si-meta-model">${esc(img.model)}</div>` : '') +
        `</div>` : '') +
      (img.prompt ? `<div class="si-prompt-row" onclick="toggleSampleSend(this,${idx},'pos')">` +
        `<div class="si-prompt-label">Prompt</div>` +
        `<div class="si-prompt-text">${esc(img.prompt)}</div>` +
        `<div class="trained-word-send">+</div></div>` : '') +
      (img.neg ? `<div class="si-prompt-row" onclick="toggleSampleSend(this,${idx},'neg')">` +
        `<div class="si-prompt-label">Neg</div>` +
        `<div class="si-prompt-text">${esc(img.neg)}</div>` +
        `<div class="trained-word-send">+</div></div>` : '') +
      `</div>`;
  }).join('');
  return `<div class="info-section">` +
    `<div class="tw-header"><div class="info-label">Sample Images</div>` +
    `<button class="tw-edit-btn" onclick="toggleSection(this)">Show</button></div>` +
    `<div class="si-list" style="display:none">${cards}</div>` +
    `</div>`;
}
function toggleSampleSend(el, idx, type) {
  if (!currentLora) return;
  const img = (currentLora.sample_images || [])[idx];
  if (!img) return;
  const text = type === 'pos' ? img.prompt : img.neg;
  if (!text) return;
  const key = idx + '_' + type;
  const sendEl = el.querySelector('.trained-word-send');
  if (activeSampleSends.has(key)) {
    const inserted = activeSampleSends.get(key);
    if (type === 'pos') removeWordFromPrompt(text, inserted);
    else removeFromNegativePrompt(text, inserted);
    activeSampleSends.delete(key);
    el.classList.remove('tw-active');
    if (sendEl) sendEl.textContent = '+';
  } else {
    const inserted = type === 'pos' ? insertWordToPrompt(text) : insertToNegativePrompt(text);
    activeSampleSends.set(key, inserted);
    el.classList.add('tw-active');
    if (sendEl) sendEl.textContent = '−';
  }
}
function insertToNegativePrompt(text) {
  const clean = text.replace(/,\s*$/, '').trim();
  try {
    const w = getHostWindow();
    if (!w) return clean;
    const ta = w.document.querySelector('#txt2img_neg_prompt textarea');
    if (!ta) return clean;
    const pos = ta.selectionStart;
    const selEnd = ta.selectionEnd;
    const v = ta.value;
    const before = v.slice(0, pos);
    const after = v.slice(selEnd);
    const lastNonWS = before.replace(/[^\S\n]+$/, '');
    const firstNonWS = after.replace(/^[^\S\n]+/, '');
    const sepBefore = !lastNonWS ? '' : lastNonWS.endsWith(',') ? ' ' : ', ';
    const sepAfter = firstNonWS && !firstNonWS.startsWith(',') ? ', ' : '';
    const toInsert = sepBefore + clean + sepAfter;
    const newVal = before + toInsert + after;
    ta.value = newVal;
    ta.selectionStart = ta.selectionEnd = before.length + toInsert.length;
    ta.dispatchEvent(new Event('input', { bubbles: true }));
    return toInsert;
  } catch(e) { return clean; }
}
function removeFromNegativePrompt(text, inserted) {
  try {
    const w = getHostWindow();
    if (!w) return;
    const ta = w.document.querySelector('#txt2img_neg_prompt textarea');
    if (!ta) return;
    let v = ta.value;
    const idx = v.lastIndexOf(inserted);
    if (idx !== -1) {
      v = v.slice(0, idx) + v.slice(idx + inserted.length);
    } else {
      const clean = (inserted || text).replace(/^[\s,]+/, '').replace(/[\s,]+$/, '').trim();
      const escaped = clean.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      v = v.replace(new RegExp(',\\s*' + escaped), '')
           .replace(new RegExp(escaped + '\\s*,\\s*'), '')
           .replace(new RegExp(escaped), '');
    }
    ta.value = v.trim().replace(/^,\s*/, '').replace(/,\s*$/, '');
    ta.dispatchEvent(new Event('input', { bubbles: true }));
  } catch(e) {}
}
function abbrevModel(s) {
  return (s || '')
    .replace(/Illustrious/gi, 'IL')
    .replace(/Pony Diffusion/gi, 'Pony')
    .replace(/Stable Diffusion/gi, 'SD');
}

// ソート設定を起動前に復元し、loadLoras()が正しいソートで動作するようにする
sortBy = getSetting('sort_by', 'path');
sortDir = getSetting('sort_dir', 'asc');
(function() {
  const sel = document.getElementById('sort-by');
  if (sel) sel.value = sortBy;
  const dirBtn = document.getElementById('sort-dir-btn');
  if (dirBtn) dirBtn.textContent = sortDir === 'asc' ? '↑' : '↓';
})();
loadLoras().then(initSettings);
</script>
</body>
</html>"""


def _get_lora_dir():
    cfg = _load_config()
    if cfg.get("lora_dir"):
        p = Path(cfg["lora_dir"])
        if p.exists():
            return p
    try:
        import modules.shared as shared
        if hasattr(shared, 'opts') and getattr(shared.opts, 'lora_dir', None):
            return Path(shared.opts.lora_dir)
        if hasattr(shared, 'cmd_opts') and getattr(shared.cmd_opts, 'lora_dir', None):
            return Path(shared.cmd_opts.lora_dir)
    except Exception:
        pass
    return LORA_DIR


def _scan_loras():
    lora_dir = _get_lora_dir()
    loras = []
    if not lora_dir.exists():
        return loras

    for path in sorted(lora_dir.rglob("*.safetensors")):
        name = path.stem
        rel = path.relative_to(lora_dir)
        category = rel.parent.as_posix() if rel.parent.as_posix() != '.' else ''

        preview_rel = None
        for pext in [".preview.png", ".preview.jpg", ".preview.jpeg", ".preview.webp"]:
            ppath = path.parent / (name + pext)
            if ppath.exists():
                preview_rel = (path.parent / (name + pext)).relative_to(lora_dir).as_posix()
                break

        activation_text = ""
        preferred_weight = 1.0
        custom_trigger_words = None
        custom_model_name = None
        custom_tags = None
        json_path = path.parent / (name + ".json")
        if json_path.exists():
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                activation_text = data.get("activation text", "")
                w = data.get("preferred weight", 1.0)
                preferred_weight = float(w) if w else 1.0
                if "trigger_words" in data:
                    custom_trigger_words = data["trigger_words"]
                if "model_name" in data:
                    custom_model_name = data["model_name"]
                if "tags" in data:
                    custom_tags = data["tags"]
            except Exception:
                pass

        model_name = name
        tags = []
        base_model = ""
        civitai_model_id = 0
        civitai_version_id = 0
        trained_words = []
        sample_images = []
        civitai_html = ""
        import re as _re

        def _sanitize_html(raw):
            s = _re.sub(r'<(script|iframe|object|embed|style|form)[^>]*>.*?</\1>', '', raw, flags=_re.DOTALL|_re.IGNORECASE)
            s = _re.sub(r'\son\w+\s*=\s*"[^"]*"', '', s, flags=_re.IGNORECASE)
            s = _re.sub(r"\son\w+\s*=\s*'[^']*'", '', s, flags=_re.IGNORECASE)
            return s.strip()

        def _parse_images(images_list):
            result = []
            for img in (images_list or []):
                url = img.get("url", "")
                if not url or img.get("type", "image") != "image" or len(result) >= 6:
                    continue
                meta = img.get("meta") or {}
                result.append({
                    "url": url,
                    "prompt": (meta.get("prompt") or "")[:2000],
                    "neg": (meta.get("negativePrompt") or "")[:2000],
                    "steps": meta.get("steps", ""),
                    "cfg": meta.get("cfgScale", ""),
                    "sampler": (meta.get("sampler") or "")[:40],
                    "model": (meta.get("Model") or meta.get("model") or "")[:60],
                    "seed": meta.get("seed", ""),
                    "size": (meta.get("Size") or "")[:20],
                })
            return result

        meta_path = path.parent / (name + ".metadata.json")
        info_path = path.parent / (name + ".civitai.info")
        if meta_path.exists():
            try:
                mdata = json.loads(meta_path.read_text(encoding="utf-8"))
                model_name = mdata.get("model_name", name)
                tags = mdata.get("tags", [])
                base_model = mdata.get("base_model", "")
                if not preview_rel:
                    purl = mdata.get("preview_url", "")
                    if purl:
                        ppath = Path(purl)
                        if ppath.exists():
                            try:
                                preview_rel = ppath.relative_to(lora_dir).as_posix()
                            except ValueError:
                                pass
                civitai = mdata.get("civitai") or {}
                civitai_model_id = int(civitai.get("modelId") or 0)
                civitai_version_id = int(civitai.get("id") or 0)
                trained_words = civitai.get("trainedWords") or []
                raw_desc = mdata.get("modelDescription") or civitai.get("description") or ""
                civitai_html = _sanitize_html(raw_desc)
                sample_images = _parse_images(civitai.get("images"))
            except Exception:
                pass
        elif info_path.exists():
            try:
                idata = json.loads(info_path.read_text(encoding="utf-8"))
                minfo = idata.get("model") or {}
                model_name = minfo.get("name") or name
                tags = minfo.get("tags") or []
                base_model = idata.get("baseModel") or ""
                civitai_model_id = int(idata.get("modelId") or 0)
                civitai_version_id = int(idata.get("id") or 0)
                trained_words = idata.get("trainedWords") or []
                raw_desc = minfo.get("description") or idata.get("description") or ""
                civitai_html = _sanitize_html(raw_desc)
                sample_images = _parse_images(idata.get("images"))
            except Exception:
                pass

        # apply custom overrides regardless of whether metadata files exist
        if custom_model_name:
            model_name = custom_model_name
        if custom_tags is not None:
            tags = custom_tags
        if custom_trigger_words is not None:
            trained_words = custom_trigger_words

        loras.append({
            "name": name,
            "model_name": model_name,
            "category": category,
            "file_path": str(path),
            "file_date": path.stat().st_ctime,
            "activation_text": activation_text,
            "preferred_weight": preferred_weight,
            "tags": tags,
            "base_model": base_model,
            "preview": preview_rel,
            "civitai_model_id": civitai_model_id,
            "civitai_version_id": civitai_version_id,
            "trained_words": trained_words,
            "sample_images": sample_images,
            "civitai_html": civitai_html,
        })

    return loras


def _register_api(_, app: FastAPI):
    lora_dir_resolved = _get_lora_dir().resolve()

    @app.get("/lora_browser/ui", response_class=HTMLResponse)
    def ui():
        return HTMLResponse(
            content=HTML_PAGE,
            headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}
        )

    @app.get("/lora_browser/list")
    def list_loras():
        loras = _scan_loras()
        lora_dir = _get_lora_dir()
        folders = []
        if lora_dir.exists():
            for d in sorted(lora_dir.rglob("*")):
                if d.is_dir():
                    rel = str(d.relative_to(lora_dir)).replace("\\", "/")
                    if rel and not any(p.startswith(".") for p in Path(rel).parts):
                        folders.append(rel)
        no_cache = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}
        return JSONResponse(content={"loras": loras, "folders": folders}, headers=no_cache)

    @app.post("/lora_browser/create_folder")
    async def create_folder(request: Request):
        data = await request.json()
        folder_path = data.get("path", "").strip()
        if not folder_path or ".." in folder_path:
            return JSONResponse(status_code=400, content={"error": "Invalid path"})
        lora_dir = _get_lora_dir()
        target = lora_dir / folder_path
        try:
            target.resolve().relative_to(lora_dir.resolve())
        except ValueError:
            return JSONResponse(status_code=400, content={"error": "Invalid path"})
        target.mkdir(parents=True, exist_ok=True)
        return JSONResponse(content={"ok": True})

    @app.post("/lora_browser/delete_folder")
    async def delete_folder_api(request: Request):
        data = await request.json()
        folder_path = data.get("path", "").strip()
        if not folder_path or ".." in folder_path:
            return JSONResponse(status_code=400, content={"error": "Invalid path"})
        lora_dir = _get_lora_dir()
        target = lora_dir / folder_path
        try:
            target.resolve().relative_to(lora_dir.resolve())
        except ValueError:
            return JSONResponse(status_code=400, content={"error": "Invalid path"})
        if not target.exists() or not target.is_dir():
            return JSONResponse(status_code=404, content={"error": "Folder not found"})
        sf_files = list(target.rglob("*.safetensors"))
        if sf_files:
            return JSONResponse(status_code=400, content={"error": f"Folder contains {len(sf_files)} LORA(s). Move them first."})
        import shutil as _shutil
        _shutil.rmtree(str(target))
        return JSONResponse(content={"ok": True})

    @app.post("/lora_browser/rename")
    async def rename_lora(request: Request):
        data = await request.json()
        name = data.get("name", "")
        new_model_name = (data.get("model_name") or "").strip()
        if not name or not new_model_name or any(c in name for c in ('/', '\\', '..')):
            return JSONResponse(status_code=400, content={"error": "Invalid"})
        lora_dir = _get_lora_dir()
        for sf in lora_dir.rglob(name + ".safetensors"):
            json_path = sf.parent / (name + ".json")
            try:
                existing = {}
                if json_path.exists():
                    existing = json.loads(json_path.read_text(encoding="utf-8"))
                existing["model_name"] = new_model_name
                json_path.write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                return JSONResponse(content={"ok": True})
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
        return JSONResponse(status_code=404, content={"error": "Not found"})

    @app.post("/lora_browser/rename_file")
    async def rename_file_endpoint(request: Request):
        data = await request.json()
        old_name = (data.get("name") or "").strip()
        new_name = (data.get("new_name") or "").strip()
        bad = set('/\\:*?"<>|')
        if not old_name or not new_name or any(c in bad for c in old_name + new_name) or '..' in new_name:
            return JSONResponse(status_code=400, content={"error": "Invalid name"})
        lora_dir = _get_lora_dir()
        for sf in lora_dir.rglob(old_name + ".safetensors"):
            parent = sf.parent
            if (parent / (new_name + ".safetensors")).exists():
                return JSONResponse(status_code=400, content={"error": "File already exists"})
            try:
                for ext in [".safetensors", ".json", ".metadata.json",
                            ".preview.png", ".preview.jpg", ".preview.jpeg"]:
                    old_p = parent / (old_name + ext)
                    if old_p.exists():
                        old_p.rename(parent / (new_name + ext))
                return JSONResponse(content={"ok": True})
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": str(e)})
        return JSONResponse(status_code=404, content={"error": "Not found"})

    @app.post("/lora_browser/save_tags")
    async def save_tags_endpoint(request: Request):
        data = await request.json()
        name = data.get("name", "")
        tags = data.get("tags", [])
        if not name or any(c in name for c in ('/', '\\', '..')):
            return JSONResponse(status_code=400, content={"error": "Invalid name"})
        lora_dir = _get_lora_dir()
        target_json = None
        for sf in lora_dir.rglob(name + ".safetensors"):
            target_json = sf.parent / (name + ".json")
            break
        if target_json is None:
            return JSONResponse(status_code=404, content={"error": "LORA not found"})
        try:
            existing = {}
            if target_json.exists():
                existing = json.loads(target_json.read_text(encoding="utf-8"))
            existing["tags"] = tags
            target_json.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return JSONResponse(content={"ok": True})
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    @app.post("/lora_browser/save_trigger_words")
    async def save_trigger_words(request: Request):
        data = await request.json()
        name = data.get("name", "")
        words = data.get("words", [])
        if not name or any(c in name for c in ('/', '\\', '..')):
            return JSONResponse(status_code=400, content={"error": "Invalid name"})
        lora_dir = _get_lora_dir()
        target_json = None
        for sf in lora_dir.rglob(name + ".safetensors"):
            target_json = sf.parent / (name + ".json")
            break
        if target_json is None:
            return JSONResponse(status_code=404, content={"error": "LORA not found"})
        try:
            existing = {}
            if target_json.exists():
                existing = json.loads(target_json.read_text(encoding="utf-8"))
            existing["trigger_words"] = words
            target_json.write_text(
                json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            return JSONResponse(content={"ok": True})
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    @app.delete("/lora_browser/delete")
    def delete_lora(name: str):
        if not name or any(c in name for c in ('/', '\\', '..')):
            return JSONResponse(status_code=400, content={"error": "Invalid name"})
        lora_dir = _get_lora_dir()
        for sf in lora_dir.rglob(name + ".safetensors"):
            deleted = []
            for ext in [".safetensors", ".json", ".metadata.json",
                        ".preview.png", ".preview.jpg", ".preview.jpeg"]:
                p = sf.parent / (sf.stem + ext)
                if p.exists():
                    p.unlink()
                    deleted.append(p.name)
            return JSONResponse(content={"ok": True, "deleted": deleted})
        return JSONResponse(status_code=404, content={"error": "Not found"})

    @app.post("/lora_browser/move_lora")
    async def move_lora(request: Request):
        data = await request.json()
        name = data.get("name", "")
        target_folder = data.get("target_folder", "")
        if not name or any(c in name for c in ('\\', '/', '..')):
            return JSONResponse(status_code=400, content={"error": "Invalid name"})
        lora_dir = _get_lora_dir()
        source_sf = None
        for sf in lora_dir.rglob(name + ".safetensors"):
            source_sf = sf
            break
        if not source_sf or not source_sf.exists():
            return JSONResponse(status_code=404, content={"error": "LORA not found"})
        if target_folder:
            target_dir = lora_dir / target_folder
            try:
                target_dir.resolve().relative_to(lora_dir.resolve())
            except ValueError:
                return JSONResponse(status_code=400, content={"error": "Invalid target path"})
        else:
            target_dir = lora_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        parent = source_sf.parent
        moved = []
        for ext in [".safetensors", ".json", ".metadata.json", ".civitai.info",
                    ".preview.png", ".preview.jpg", ".preview.jpeg", ".preview.webp",
                    ".png", ".jpg", ".jpeg", ".webp"]:
            p = parent / (name + ext)
            if p.exists():
                new_path = target_dir / p.name
                if not new_path.exists():
                    p.rename(new_path)
                    moved.append(p.name)
        return JSONResponse(content={"ok": True, "moved": moved})

    @app.post("/lora_browser/set_preview")
    async def set_preview(request: Request):
        import base64 as b64mod
        data = await request.json()
        name = (data.get("name") or "").strip()
        image_b64 = (data.get("image") or "").strip()
        ext = (data.get("ext") or "png").lower()
        if ext not in ("png", "jpg", "jpeg", "webp"):
            ext = "png"
        if not name or not image_b64:
            return JSONResponse(status_code=400, content={"error": "Missing data"})
        lora_dir = _get_lora_dir()
        for sf in lora_dir.rglob(name + ".safetensors"):
            img_bytes = b64mod.b64decode(image_b64)
            preview_path = sf.parent / (sf.stem + f".preview.{ext}")
            preview_path.write_bytes(img_bytes)
            return JSONResponse(content={"ok": True})
        return JSONResponse(status_code=404, content={"error": "LORA not found"})

    @app.get("/lora_browser/open_folder")
    def open_folder(name: str):
        if not name or any(c in name for c in ('/', '\\', '..')):
            return JSONResponse(status_code=400, content={"error": "Invalid name"})
        lora_dir = _get_lora_dir()
        for sf in lora_dir.rglob(name + ".safetensors"):
            import subprocess
            subprocess.Popen(['explorer', '/select,', str(sf)])
            return JSONResponse(content={"ok": True})
        return JSONResponse(status_code=404, content={"error": "Not found"})

    @app.get("/lora_browser/preview")
    def preview(path: str, w: int = 0):
        safe = (lora_dir_resolved / path).resolve()
        if not str(safe).startswith(str(lora_dir_resolved)):
            return JSONResponse(status_code=403, content={"error": "Forbidden"})
        if not safe.exists():
            return JSONResponse(status_code=404, content={"error": "Not found"})
        no_cache = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}
        if w <= 0 or w > 2048:
            return FileResponse(str(safe), headers=no_cache)
        try:
            from PIL import Image
            from io import BytesIO
            from fastapi.responses import Response as FastAPIResponse
            img = Image.open(str(safe))
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            if img.width > w:
                h = int(img.height * w / img.width)
                img = img.resize((w, h), Image.LANCZOS)
            buf = BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=88, optimize=True)
            buf.seek(0)
            return FastAPIResponse(content=buf.getvalue(), media_type="image/jpeg", headers=no_cache)
        except Exception:
            import mimetypes
            mt = mimetypes.guess_type(str(safe))[0] or "image/jpeg"
            with open(str(safe), "rb") as f:
                raw = f.read()
            if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
                mt = "image/webp"
            from fastapi.responses import Response as FastAPIResponse
            return FastAPIResponse(content=raw, media_type=mt, headers=no_cache)

    @app.get("/lora_browser/civitai_missing")
    def civitai_missing():
        lora_dir = _get_lora_dir()
        result = []
        for sf in sorted(lora_dir.rglob("*.safetensors")):
            has_meta = (sf.parent / (sf.stem + ".metadata.json")).exists()
            result.append({"name": sf.stem, "has_meta": has_meta})
        return JSONResponse(content={"loras": result})

    @app.post("/lora_browser/fetch_civitai")
    async def fetch_civitai_endpoint(request: Request):
        import hashlib
        import urllib.request as _urlreq
        import urllib.error as _urlerr
        data = await request.json()
        name = (data.get("name") or "").strip()
        force = bool(data.get("force", False))
        dl_preview = bool(data.get("dl_preview", True))

        if not name or any(c in name for c in ('/', '\\', '..')):
            return JSONResponse(status_code=400, content={"error": "Invalid name"})

        lora_dir = _get_lora_dir()
        sf_path = None
        for sf in lora_dir.rglob(name + ".safetensors"):
            sf_path = sf
            break
        if not sf_path:
            return JSONResponse(status_code=404, content={"error": "LORA not found"})

        meta_path = sf_path.parent / (name + ".metadata.json")
        info_path = sf_path.parent / (name + ".civitai.info")
        if meta_path.exists() and not force:
            return JSONResponse(content={"ok": True, "skipped": True})

        # Try to get SHA256 from .civitai.info first
        sha256 = None
        if info_path.exists():
            try:
                idata = json.loads(info_path.read_text(encoding="utf-8"))
                for f in (idata.get("files") or []):
                    h = (f.get("hashes") or {}).get("SHA256", "")
                    if h:
                        sha256 = h.lower()
                        break
            except Exception:
                pass

        if not sha256:
            try:
                h = hashlib.sha256()
                with open(sf_path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                sha256 = h.hexdigest()
            except Exception as e:
                return JSONResponse(status_code=500, content={"error": f"Hash error: {e}"})

        api_key = request.headers.get("X-Civitai-Api-Key", "").strip()
        def _civitai_headers():
            h = {"User-Agent": "sd-webui-lora-browser/1.0"}
            if api_key:
                h["Authorization"] = f"Bearer {api_key}"
            return h

        try:
            api_url = f"https://civitai.com/api/v1/model-versions/by-hash/{sha256}"
            req = _urlreq.Request(api_url, headers=_civitai_headers())
            with _urlreq.urlopen(req, timeout=20) as resp:
                ver_data = json.loads(resp.read().decode("utf-8"))
        except _urlerr.HTTPError as e:
            if e.code == 404:
                return JSONResponse(status_code=404, content={"error": "Not found on CivitAI"})
            return JSONResponse(status_code=502, content={"error": f"CivitAI API error: {e.code}"})
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": f"Network error: {e}"})

        model_info = ver_data.get("model") or {}
        images = [img for img in (ver_data.get("images") or []) if img.get("type", "image") == "image"]

        # model-versions/by-hash often omits model.description and tags; fetch separately
        model_description = model_info.get("description") or ""
        model_tags = model_info.get("tags") or []
        if not model_description or not model_tags:
            model_id = ver_data.get("modelId")
            if model_id:
                try:
                    mreq = _urlreq.Request(
                        f"https://civitai.com/api/v1/models/{model_id}",
                        headers=_civitai_headers()
                    )
                    with _urlreq.urlopen(mreq, timeout=20) as resp:
                        mdata = json.loads(resp.read().decode("utf-8"))
                    if not model_description:
                        model_description = mdata.get("description") or ""
                    if not model_tags:
                        model_tags = mdata.get("tags") or []
                except Exception:
                    pass

        metadata = {
            "model_name": model_info.get("name") or name,
            "tags": model_tags,
            "base_model": ver_data.get("baseModel") or "",
            "preview_url": "",
            "civitai": {
                "modelId": ver_data.get("modelId"),
                "id": ver_data.get("id"),
                "trainedWords": ver_data.get("trainedWords") or [],
                "description": ver_data.get("description") or "",
                "images": images[:10],
            },
            "modelDescription": model_description,
        }

        if dl_preview and images:
            has_preview = any(
                (sf_path.parent / (name + ext)).exists()
                for ext in [".preview.png", ".preview.jpg", ".preview.jpeg", ".preview.webp"]
            )
            if not has_preview:
                try:
                    img_url = images[0].get("url", "")
                    if img_url:
                        req = _urlreq.Request(img_url, headers={"User-Agent": "sd-webui-lora-browser/1.0"})
                        with _urlreq.urlopen(req, timeout=30) as resp:
                            img_data = resp.read()
                            ct = resp.headers.get("Content-Type", "")
                        if "webp" in ct:
                            img_ext = ".preview.webp"
                        elif "png" in ct:
                            img_ext = ".preview.png"
                        else:
                            img_ext = ".preview.jpg"
                        (sf_path.parent / (name + img_ext)).write_bytes(img_data)
                except Exception:
                    pass

        try:
            meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"Save error: {e}"})

        # update .json with activation text for civitai helper compatibility
        trained_words = ver_data.get("trainedWords") or []
        if trained_words:
            json_path = sf_path.parent / (name + ".json")
            try:
                existing = {}
                if json_path.exists():
                    existing = json.loads(json_path.read_text(encoding="utf-8"))
                existing["activation text"] = ", ".join(trained_words)
                json_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

        return JSONResponse(content={"ok": True, "model_name": metadata["model_name"]})

    @app.get("/lora_browser/config")
    def get_config():
        return JSONResponse(content=_load_config())

    @app.post("/lora_browser/config")
    async def save_config_endpoint(request: Request):
        data = await request.json()
        _save_config(data)
        return JSONResponse(content={"ok": True})


def _create_tab():
    import gradio as gr
    css = "#lora-open-btn { min-height: 44px !important; font-size: 14px !important; font-weight: 600 !important; }"
    with gr.Blocks(analytics_enabled=False, css=css) as ui:
        btn = gr.Button('Open in New Window', variant='primary', elem_id='lora-open-btn')
        btn.click(
            fn=None,
            inputs=[],
            outputs=[],
            js="() => window.open('/lora_browser/ui', 'lora_browser', 'width=1280,height=860,resizable=yes,scrollbars=yes')"
        )
        gr.HTML('''
            <iframe src="/lora_browser/ui"
                    style="width:100%;height:calc(100vh - 160px);border:none;display:block;margin-top:8px;">
            </iframe>
        ''')
    return [(ui, 'LORA Browser', 'lora_browser_tab')]


on_app_started(_register_api)
on_ui_tabs(_create_tab)
