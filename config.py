import os

# OAUTH2
AUTHORIZE_URL = os.getenv("AUTHORIZE_URL", "http://pastabytes.test:8080/oauth/authorize")
TOKEN_URL = os.getenv("TOKEN_URL", "http://pastabytes.test:8080/oauth/token")
REFRESH_TOKEN_URL = os.getenv("REFRESH_TOKEN_URL", "http://pastabytes.test:8080/oauth/token")
REVOKE_TOKEN_URL = os.getenv("REVOKE_TOKEN_URL", "http://pastabytes.test:8080/oauth/revoke")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://encounter.pastabytes.test:8501")
SCOPE = "read"

# PIXELFED
PIXELFED_BASE_URL = os.getenv("PIXELFED_BASE_URL", "pastabytes.test:8080")
PIXELFED_BASE_URL_SCHEME = os.getenv("PIXELFED_BASE_URL_SCHEME", "http")

# SEMANTIC REPOSITORIES
AVIO_SPARQL_ENDPOINT = os.getenv("AVIO_SPARQL_ENDPOINT", "http://localhost:8890/sparql")
AVIO_SPARQL_AUTH_ENDPOINT = os.getenv("AVIO_SPARQL_AUTH_ENDPOINT", "http://localhost:8890/sparql-auth")
DBPEDIA_SPARQL_ENDPOINT = os.getenv("DBPEDIA_SPARQL_ENDPOINT", "http://dbpedia.org/sparql")

# CREDENTIALS
LOCAL_SPARQL_USER = os.getenv("LOCAL_SPARQL_USER")
LOCAL_SPARQL_PASSWORD = os.getenv("LOCAL_SPARQL_PASSWORD")

# SEMANTIC CONTEXT
PASTABYTES_ENCOUNTER = os.getenv("PASTABYTES_ENCOUNTER", "https://encounter.pastabytes.com")

# OTHER
APP_TITLE = os.getenv("APP_TITLE", "Encounter")