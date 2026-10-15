#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
CERTS_DIR="$DIR/certs"
mkdir -p "$CERTS_DIR"

DOMAIN="${1:-localhost}"
DAYS="${2:-365}"

echo "Đang tạo chứng chỉ SSL cho: $DOMAIN ..."
openssl req -x509 -nodes -days "$DAYS" -newkey rsa:2048 \
    -keyout "$CERTS_DIR/key.pem" \
    -out "$CERTS_DIR/cert.pem" \
    -subj "/C=VN/ST=HCM/L=HCM/O=TinHocEducation/CN=$DOMAIN" \
    -addext "subjectAltName=DNS:$DOMAIN,IP:127.0.0.1"

echo "Tạo chứng chỉ SSL thành công tại $CERTS_DIR!"
