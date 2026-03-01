# AtCoder Rating Widget

<img src="./img/widget-saple.png" width="422" alt="生成されるウィジェットの例">

## 概要

AtCoder のユーザーページから取得できる履歴 JSON を元に、ユーザーごとの「レーティング表示ウィジェット（HTML）」を自動生成します。

- HTML に埋め込み可能（`<object>` 等）
- Algorithm / Heuristic の両方に対応
- 1日に一度 Gihub Actions でレーティングを自動更新
- ウィジェット全体クリックで AtCoder のユーザーページへ遷移
- Heuristic 部分クリックで `contestType=heuristic` のページへ遷移

## 使い方

### 1. リポジトリをクローン

以下のコマンドでリポジトリをクローンしてください。
```bash
git clone https://github.com/r-1317/AtCoder-Rating-Widget.git
cd AtCoder-Rating-Widget
```
次に、GitHubにあなたのリモートリポジトリを作成してください。
upstream などの設定をしていただいても構いませんが、面倒な方は`.git/`ディレクトリを一度削除してから新たにリポジトリを初期化してください。

### 2. `users-list` を編集

`users-list` に、ウィジェットを生成したい AtCoder ユーザ名を改行区切りで記入します。

- 空行は無視されます
- `#` から始まる行はコメントとして無視されます

### 3. 手動で`generate_widgets.py`を実行 (初回のみ)
ローカル環境で`generate_widgets.py`を実行してください。

```bash
python3 generate_widgets.py
```

実行後、変更をコミットして GitHub に push してください。

#### 補足
`generate_widgets.py`はGitHub Actionsにて自動で実行されるようになっておりますので、 以後手動で実行する必要はございません。


### 4. GitHub Pages を有効化

GitHub のリポジトリ画面から、以下を設定します。

- Settings → Pages
- Build and deployment の Source を `Deploy from a branch` に設定
- Branch を `main` / `(root)` に設定して Save

（反映まで数分かかることがあります）

### 5. 埋め込み

生成されたウィジェットは GitHub Pages 上で配信されます。任意の HTML に、以下のように埋め込めます。

```html
<object data="https://{あなたのgithubユーザ名}.github.io/AtCoder-Rating-Widget/widgets/{AtCoderユーザ名}.html" type="text/html" width="320" height="160"></object>
```

`width`と`height`は環境によって最適な値が異なりますので、適宜調整してお使いください。

## ライセンス

このソフトウェアは、[MIT License](https://opensource.org/license/mit/)の下で配布されています。詳細は[LICENSE](./LICENSE)を参照してください。

<!-- --- -->

Copyright © 2026 [r-1317](https://github.com/r-1317) All Rights Reserved.
