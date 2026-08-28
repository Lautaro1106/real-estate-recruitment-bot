from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import os

app = Flask(__name__)


@app.route('/verify', methods=['POST'])
def verify():
    secret = os.environ.get('WEBHOOK_SECRET_SCHEDULING', '')
    signature = request.headers.get('x-cal-signature-256', '')

    if not secret:
        return jsonify({'valid': False, 'error': 'Secret no configurado'}), 500

    if not signature:
        return jsonify({'valid': False, 'error': 'Firma ausente'}), 401

    parsed_body = request.get_json(force=True)
    raw_body = json.dumps(parsed_body, separators=(',', ':'), ensure_ascii=False)

    expected = hmac.new(
        secret.encode('utf-8'),
        raw_body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(signature, expected):
        return jsonify({'valid': True}), 200
    else:
        return jsonify({'valid': False, 'error': 'Firma inválida'}), 401


@app.route('/verify/chatwoot', methods=['POST'])
def verify_chatwoot():
    secret = os.environ.get('WEBHOOK_SECRET_MESSAGING', '')
    signature = request.headers.get('x-chatwoot-signature', '')
    timestamp = request.headers.get('x-chatwoot-timestamp', '')

    if not secret:
        return jsonify({'valid': False, 'error': 'Secret no configurado'}), 500

    if not signature:
        return jsonify({'valid': False, 'error': 'Firma ausente'}), 401

    raw_body = request.get_data()
    message = f"{timestamp}.".encode() + raw_body

    expected = "sha256=" + hmac.new(
        secret.encode('utf-8'),
        message,
        hashlib.sha256
    ).hexdigest()

    if hmac.compare_digest(signature, expected):
        return jsonify({'valid': True}), 200
    else:
        return jsonify({'valid': False, 'error': 'Firma inválida'}), 401


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
