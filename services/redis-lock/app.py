import os
import redis
from flask import Flask, request, jsonify

app = Flask(__name__)

REDIS_URL      = os.environ.get('REDIS_URL', 'redis://localhost:6379')
TTL_SECONDS    = int(os.environ.get('LOCK_TTL_SECONDS', '10'))
INTERNAL_TOKEN = os.environ.get('INTERNAL_TOKEN', '')


def get_redis():
    return redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=2)


def check_token():
    if not INTERNAL_TOKEN:
        return False
    return request.headers.get('X-Internal-Token', '') == INTERNAL_TOKEN


@app.route('/health', methods=['GET'])
def health():
    try:
        r = get_redis()
        r.ping()
        return jsonify({'status': 'ok', 'redis': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'detail': str(e)}), 503


@app.route('/acquire', methods=['POST'])
def acquire():
    if not check_token():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    message_id   = data.get('message_id', '').strip()
    phone_number = data.get('phone_number', '').strip()

    if not message_id or not phone_number:
        return jsonify({
            'acquired': False,
            'error': 'message_id y phone_number son requeridos'
        }), 400

    key_msg   = f'lock:msg:{message_id}'
    key_phone = f'lock:phone:{phone_number}'

    try:
        r = get_redis()

        msg_acquired   = r.set(key_msg,   '1', ex=TTL_SECONDS, nx=True)
        phone_acquired = r.set(key_phone, '1', ex=TTL_SECONDS, nx=True)

        if msg_acquired and phone_acquired:
            return jsonify({'acquired': True}), 200

        if msg_acquired:
            r.delete(key_msg)
        if phone_acquired:
            r.delete(key_phone)

        return jsonify({
            'acquired': False,
            'reason': 'message_id duplicado' if not msg_acquired else 'phone_number en proceso'
        }), 423

    except redis.RedisError as e:
        app.logger.error(f'Redis error en /acquire: {e}')
        return jsonify({'acquired': True, 'warning': 'Redis no disponible, procesando sin lock'}), 200


@app.route('/release', methods=['POST'])
def release():
    if not check_token():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    phone_number = data.get('phone_number', '').strip()

    if not phone_number:
        return jsonify({
            'released': False,
            'error': 'phone_number es requerido'
        }), 400

    key_phone = f'lock:phone:{phone_number}'

    try:
        r = get_redis()
        r.delete(key_phone)
        return jsonify({'released': True}), 200

    except redis.RedisError as e:
        app.logger.error(f'Redis error en /release: {e}')
        return jsonify({'released': False, 'warning': str(e)}), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=False)
