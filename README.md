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

## 📖 使用方法

### 1. ユーザー登録・ログイン
1. ブラウザでアプリケーションにアクセス
2. 「Sign Up」でアカウントを作成
3. 作成したアカウントでログイン

### 2. VRMモデルのアップロード
1. 「Upload Model」セクションでVRMファイルを選択
2. モデル名を入力
3. オプション: VRMAアニメーションファイルも同時にアップロード可能
4. 「Upload」ボタンをクリック

### 3. 背景画像の変更
1. 「Upload Background」セクションで画像ファイルを選択
2. サポート形式: JPG、PNG、GIF
3. アップロード後、背景選択リストから適用

### 4. 3Dビューアーの操作
- **マウス左ドラッグ**: カメラの回転
- **マウスホイール**: ズームイン/アウト
- **アニメーション選択**: ドロップダウンからアニメーションを選択・再生

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
