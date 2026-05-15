# sd-webui-lora-browser

Stable Diffusion WebUI / Forge / Reforge 向けの LORA ブラウザ拡張機能です。

## 機能

- サムネイル付きでLORAファイルを一覧表示・検索
- LORAファイルの移動（Ctrl+クリックで複数選択可）
- LORAの構文やトリガーワードをtxt2imgに送信
- undo機能搭載なので簡単にトリガーワードの追加や消去が可能
- 専用ウィンドウで快適に操作できます
- CivitAIからメタデータ（モデル名・トリガーワード・タグ・説明・プレビュー画像）を取得

## インストール方法

1. WebUI を起動
2. **Extensions** タブ → **Install from URL** を開く
3. 以下のURLを貼り付けて Install をクリック：
   ```
   https://github.com/ranran141/sd-webui-lora-browser
   ```
4. WebUIを再起動
5. **LORA Browser** タブが作成されていればインストール完了

## 動作環境

- Stable Diffusion WebUI Forge NEO
- Stable Diffusion WebUI Reforge

## 更新履歴

### v1.2 (2026-05-16)
- Reforge / Forge NEO 対応

### v1.1.0 (2026-05-15)
- civitaiからメタデータ取得に対応
- 最近使ったLORAを表示
- LORAフォルダ指定を追加

### v1.0.0 (2026-05-14)
- 初回リリース
