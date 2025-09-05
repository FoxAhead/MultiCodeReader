from flask_socketio import SocketIO, emit, join_room, leave_room
from .models import db, Box, BoxCode
from .services.box_service import BoxService

socketio = SocketIO(cors_allowed_origins="*")


def init_socketio(app):
    socketio.init_app(app)
    return socketio


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('join_box')
def handle_join_box(data):
    box_id = data.get('box_id')
    if box_id:
        join_room(f'box_{box_id}')
        emit('joined_box', {'box_id': box_id, 'message': f'Joined box {box_id}'})
        print(f'Client joined box {box_id}')


@socketio.on('leave_box')
def handle_leave_box(data):
    box_id = data.get('box_id')
    if box_id:
        leave_room(f'box_{box_id}')
        emit('left_box', {'box_id': box_id, 'message': f'Left box {box_id}'})


@socketio.on('get_current_box')
def handle_get_current_box():
    box = BoxService.get_current_box()
    if box:
        code_count = BoxService.get_box_code_count(box.box_id)
        emit('current_box_info', {
            'box_id': box.box_id,
            'closed': bool(box.closed),
            'code_count': code_count
        })


def broadcast_box_update(box_id):
    """Отправляет обновление информации о коробке всем подключенным клиентам"""
    box = Box.query.get(box_id)
    if box:
        code_count = BoxCode.query.filter_by(box_id=box_id).count()
        socketio.emit('box_updated', {
            'box_id': box_id,
            'closed': bool(box.closed),
            'code_count': code_count
        }, room=f'box_{box_id}')


def broadcast_code_scanned(box_id, code):
    """Отправляет уведомление о новом отсканированном коде"""
    socketio.emit('code_scanned', {
        'box_id': box_id,
        'code': code,
        'message': f'New code scanned: {code}'
    }, room=f'box_{box_id}')


def broadcast_box_cleared(box_id):
    """Отправляет уведомление об очистке коробки"""
    socketio.emit('box_cleared', {
        'box_id': box_id,
        'message': 'Box has been cleared'
    }, room=f'box_{box_id}')


def broadcast_box_closed(box_id, new_box_id):
    """Отправляет уведомление о закрытии коробки и создании новой"""
    socketio.emit('box_closed', {
        'old_box_id': box_id,
        'new_box_id': new_box_id,
        'message': f'Box {box_id} closed, new box {new_box_id} created'
    }, room=f'box_{box_id}')

    # Уведомляем также о новой коробке
    new_box = Box.query.get(new_box_id)
    if new_box:
        socketio.emit('current_box_changed', {
            'new_box_id': new_box_id,
            'closed': bool(new_box.closed),
            'code_count': 0
        })


def broadcast_all_boxes_update():
    """Отправляет обновление списка всех коробок"""
    from sqlalchemy import text
    query = text("""
        SELECT b.box_id, b.closed, COUNT(bc.code) as code_count
        FROM boxes b
        LEFT JOIN box_codes bc ON b.box_id = bc.box_id
        GROUP BY b.box_id
        ORDER BY b.box_id DESC
    """)

    result = db.session.execute(query)
    boxes = []

    for row in result:
        boxes.append({
            'box_id': row.box_id,
            'closed': bool(row.closed),
            'code_count': row.code_count
        })

    socketio.emit('all_boxes_updated', {'boxes': boxes})
