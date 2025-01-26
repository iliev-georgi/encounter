#!/usr/bin/sh

# IP=$(hostname -I)

# sed -i "s/\${HOSTNAME}/$IP/g" conf.d/encounter.conf

cp conf.d/*.conf /etc/nginx/conf.d/

streamlit run app.py --server.port 8501