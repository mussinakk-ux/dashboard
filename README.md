# 價差交易紀錄 Google Sheets 雲端永久版

上傳 GitHub：
- app.py
- requirements.txt
- .streamlit/config.toml

Streamlit Secrets 需要設定：
GOOGLE_SHEET_ID = "你的Google Sheet ID"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"

請把 Google Sheet 分享給 service account 的 client_email，權限設為編輯者。
