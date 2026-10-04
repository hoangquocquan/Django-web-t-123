# AI搭載 自動車部品販売プラットフォーム

[English](README.md) | 日本語

Django、React、RAG、AI Sales Assistant、n8n、LINEを組み合わせた個人開発の技術ポートフォリオプロジェクトです。

自動車部品の検索、AIによる販売支援、見積依頼（RFQ）を扱います。AWS関連の内容は、明記がない限りステージングまたはターゲット構成であり、本番稼働を意味しません。

技術スタックは Django / REST API、React / Vite、PostgreSQL、Docker、RAG、n8n、LINE、GitHub Actions、AWS staging/target architecture です。個人開発として、バックエンド、データモデリング、マイグレーション、フロントエンド連携、AI/RAG、RFQ/CRM、テスト/CI、デバッグ、レビュー、検証を担当しました。

AIコーディングツールは実装とレビューの補助として利用しましたが、テスト、API検証、マイグレーション確認、ビルド、CI向けチェックでコードを確認しています。

詳細は [アーキテクチャ資料](docs/architecture/ARCHITECTURE.md) と [ポートフォリオ整理レポート](docs/internal/RECRUITER_PORTFOLIO_CLEANUP_REPORT.md) を参照してください。

## スクリーンショット

以下の画像は、架空のデモデータを使用してローカル環境で稼働中のアプリケーションから取得しました。

![製品ページ](docs/images/product-page.png)

![AI Sales Assistant](docs/images/ai-sales-chatbot.png)

![RFQワークフロー](docs/images/rfq-workflow.png)

![管理画面](docs/images/admin-operations.png)
