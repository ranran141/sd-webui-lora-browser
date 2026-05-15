# sd-webui-lora-browser

Stable Diffusion WebUI Forge NEO 向けの LORA ブラウザ拡張機能です。

## 機能

- サムネイル付きでLORAファイルを一覧表示・検索
- ドラッグ＆ドロップでLORAのファイル移動
- LORAの構文やトリガーワードをtxt2imgに送信
- undo機能搭載なので簡単にトリガーワードの追加や消去が可能
- 別ウィンドウで開けます
- CivitAIからメタデータ（モデル名・トリガーワード・タグ・説明・プレビュー画像）を取得

## インストール方法

1. SD WebUI Forge NEO を起動
2. **Extensions** タブ → **Install from URL** を開く
3. 以下のURLを貼り付けて Install をクリック：
   ```
   https://github.com/ranran141/sd-webui-lora-browser
   ```
4. WebUIを再起動

## 動作環境

- Stable Diffusion WebUI Forge NEO

## 更新履歴

### v1.1.0
- civitaiからメタデータ取得に対応
- 最近使ったLORAを表示
- LORAフォルダ指定を追加

### v1.0.0
- 初回リリース
