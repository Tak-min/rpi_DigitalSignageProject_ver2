# 3D VRM Model Viewer & Animation System

FastAPIとThree.jsを使用した3D VRMモデルビューアー・アニメーションシステムです。VRMモデルのアップロード、表示、アニメーション再生、背景画像の変更が可能です。

## 🌟 主な機能

- **VRMモデルアップロード**: VRM形式の3Dモデルをアップロード・管理
- **アニメーション再生**: VRMAファイルによるアニメーション機能
- **背景画像変更**: カスタム背景画像のアップロード・適用
- **ユーザー認証**: 安全なユーザー管理システム
- **リアルタイム3D表示**: Three.jsベースの高品質レンダリング

## 🛠️ 技術スタック

### バックエンド
- **FastAPI**: 高性能なPython Webフレームワーク
- **SQLAlchemy**: ORM（Object-Relational Mapping）
- **SQLite**: 軽量データベース
- **Passlib**: パスワードハッシュ化
- **Python-Jose**: JWT認証

### フロントエンド
- **Three.js**: 3Dグラフィックスライブラリ
- **@pixiv/three-vrm**: VRM形式サポート
- **HTML5/CSS3/JavaScript**: モダンなWeb技術

## 📋 必要な環境

- Python 3.8以上
- pip（Pythonパッケージマネージャー）
- モダンなWebブラウザ（Chrome、Firefox、Safari、Edge）

## 🚀 セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/your-username/vrm-viewer.git
cd vrm-viewer
```

### 2. 仮想環境の作成と有効化
```bash
# Windows
python -m venv webapp
webapp\\Scripts\\activate

# macOS/Linux
python -m venv webapp
source webapp/bin/activate
```

### 3. 依存関係のインストール
```bash
pip install fastapi uvicorn sqlalchemy passlib[bcrypt] python-jose[cryptography] python-multipart Pillow
```

### 4. データベースの初期化
```bash
python init_fresh_db.py
```

### 5. サーバーの起動
```bash
python main.py
```

### 6. ブラウザでアクセス
- メインアプリケーション: http://localhost:8001
- API ドキュメント: http://localhost:8001/docs

## 📖 アプリケーション利用ガイド

このガイドでは、アプリケーションの起動から基本的な操作方法までを説明します。

### 1. 環境設定と起動方法

アプリケーションを利用するためには、まず以下の手順で環境設定とサーバーの起動を行います。

**a. 必要なライブラリのインストール**

プロジェクトに必要なライブラリを一括でインストールします。プロジェクトのルートディレクトリで、ターミナル（コマンドプロンプト）を開き、以下のコマンドを実行してください。

```bash
pip install -r requirements.txt
```

**b. FastAPIサーバーの起動**

次に、FastAPIサーバーを起動します。同じくターミナルで、以下のコマンドを実行してください。

```bash
uvicorn main:app --reload
```

`--reload`オプションを付けると、コードを変更した際に自動でサーバーが再起動され、開発に便利です。

**c. アプリケーションへのアクセス**

サーバーが正常に起動すると、ターミナルに以下のようなメッセージが表示されます。

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

このURL (`http://127.0.0.1:8000`) をウェブブラウザで開くと、アプリケーションにアクセスできます。

### 2. 基本的な使い方

アプリケーションの基本的な操作方法です。

**a. 新規ユーザー登録**

初めて利用する場合は、ユーザー登録が必要です。

1.  アプリケーション画面右上の「**Sign Up**」ボタンをクリックします。
2.  表示されたフォームに、ユーザー名とパスワードを入力し、「**Sign Up**」ボタンを押して登録を完了します。

**b. ログイン**

登録済みのユーザーは、以下の手順でログインします。

1.  アプリケーション画面右上の「**Login**」ボタンをクリックします。
2.  登録したユーザー名とパスワードを入力し、「**Login**」ボタンを押します。

**c. VRMモデルのアップロード**

ログインすると、VRMモデルをアップロードできるようになります。

1.  画面左側にある「**Upload VRM Model**」セクションの「**ファイルを選択**」ボタンをクリックし、お持ちのVRMファイル（`.vrm`）を選択します。
2.  「**Upload**」ボタンをクリックすると、モデルがアップロードされ、画面中央の3Dビューアーに表示されます。

**d. モーションの再生**

アップロードしたVRMモデルに、あらかじめ用意されたモーションを再生させることができます。

1.  画面左下の「**Play Animation**」セクションにあるドロップダウンメニューをクリックします。
2.  再生したいモーションを選択すると、3Dビューアーのモデルがそのモーションで動き始めます。

## 🔧 プロジェクト構造

```
display_project/
├── main.py              # FastAPI メインアプリケーション
├── auth.py              # 認証システム
├── crud.py              # データベース操作
├── models.py            # SQLAlchemy モデル
├── schemas.py           # Pydantic スキーマ
├── database.py          # データベース設定
├── static/              # 静的ファイル
│   ├── js/
│   │   └── main.js      # Three.js メインスクリプト
│   └── css/
│       └── style.css    # スタイルシート
├── templates/
│   └── index.html       # メインHTMLテンプレート
└── uploads/            # アップロードファイル（.gitignoreで除外）
```

## 🔐 セキュリティ機能

- JWT（JSON Web Token）による認証
- パスワードのbcryptハッシュ化
- ユーザーごとのファイル隔離
- ファイルタイプ検証
- SQLインジェクション対策

## 🧪 テスト

```bash
# 簡単な接続テスト
python quick_test.py

# 包括的なテストスイート
python comprehensive_test.py
```

## 🐛 トラブルシューティング

### ポート競合エラー
```
ERROR: [Errno 10048] error while attempting to bind on address
```
**解決方法**: main.pyのポート番号を8001から別の番号（8002、8003など）に変更

### データベースロックエラー
```bash
# データベースを再初期化
python init_fresh_db.py
```

### モジュールが見つからないエラー
```bash
# 必要なパッケージを再インストール
pip install -r requirements.txt
```

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 新しい機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📧 お問い合わせ

プロジェクトに関する質問や提案がございましたら、GitHubのIssuesでお知らせください。

## 🙏 謝辞

- [Three.js](https://threejs.org/) - 3Dグラフィックスライブラリ
- [@pixiv/three-vrm](https://github.com/pixiv/three-vrm) - VRMサポート
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能Webフレームワーク

---

🎮 **Happy 3D Modeling!** 🎮
