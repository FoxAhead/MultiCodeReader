from contextlib import contextmanager

import numpy as np
from flask import Flask, render_template, Response, jsonify
from camera_opencv import Camera
#from camera_file import Camera
from mcr_scanner import Scanner
import models
import cv2
from flask_socketio import SocketIO, emit
from base64 import b64decode

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barcode_scanner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=100000000)

models.db.init_app(app)

# Глобальные переменные для текущего состояния
current_box = None
detected_barcodes = set()


@contextmanager
def app_context():
    """Контекст для работы с приложением"""
    with app.app_context():
        yield


def init_database():
    with app.app_context():
        models.db.create_all()
        # Создаем первую коробку
        create_new_box()


def create_new_box():
    global current_box, detected_barcodes
    box = models.Box()
    models.db.session.add(box)
    models.db.session.commit()
    current_box = box
    detected_barcodes = set()
    print(f"Created new box: {box.box_number}")


def get_frame(scanner: Scanner):
    # print("get_frame 1")
    while True:
        # print("get_frame 2")
        frame = scanner.get_frame()
        # Распознаем штрихкоды
        try:
            with app_context():
                if current_box and not current_box.is_sealed:
                    for result in frame.codes:
                        barcode_text = result.text
                        if barcode_text and barcode_text not in detected_barcodes:
                            detected_barcodes.add(barcode_text)

                            # Сохраняем в базу
                            barcode = models.Barcode(code=barcode_text, box_id=current_box.id)
                            models.db.session.add(barcode)
                            models.db.session.commit()
                            # print(f"Detected barcode: {barcode_text}")
        except Exception as e:
            print(f"Error reading barcodes: {e}")

        # Кодируем frame для веб-страницы
        buffer = cv2.imencode('.jpg', frame.image)[1].tobytes()
        # print("get_frame yield")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')


@app.route('/')
def index():
    return render_template('index2.html')


@app.route('/video_feed')
def video_feed():
    return Response(get_frame(Scanner(None)), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_barcodes')
def get_barcodes():
    return jsonify({
        'barcodes': sorted(detected_barcodes),
        'box_number': current_box.box_number if current_box else None,
        'is_sealed': current_box.is_sealed if current_box else False
    })


@app.route('/clear_box', methods=['POST'])
def clear_box():
    # print("clear_box")
    create_new_box()
    emit_update_barcodes()
    return jsonify({'success': True})


@app.route('/seal_box', methods=['POST'])
def seal_box():
    # print("seal_box")
    if current_box and not current_box.is_sealed:
        current_box.is_sealed = True
        models.db.session.commit()
        create_new_box()
        return jsonify({'success': True, 'box_number': current_box.box_number})
    return jsonify({'success': False})


@socketio.on('frame_data')
def handle_frame_data(data):
    print("@socketio.on('frame_data')")
    """
    Обрабатываем кадр, полученный от клиента
    """
    try:
        # Извлекаем base64 данные изображения
        image_data = data['image']
        resolution = data['resolution']
        print(resolution)

        # Убираем префикс data:image/jpeg;base64, если есть
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        # Декодируем base64
        img_bytes = b64decode(image_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            #emit('processing_error', {'error': 'Не удалось декодировать изображение'})
            print('processing_error', {'error': 'Не удалось декодировать изображение'})
            return

        scanner = Scanner()
        frame = scanner.get_frame_by_image(img)
        # cv2.imshow('My Image', frame.image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # Распознаем штрихкоды
        try:
            with app_context():
                if current_box and not current_box.is_sealed:
                    for result in frame.codes:
                        barcode_text = result.text
                        if barcode_text and barcode_text not in detected_barcodes:
                            detected_barcodes.add(barcode_text)

                            # # Сохраняем в базу
                            # barcode = models.Barcode(code=barcode_text, box_id=current_box.id)
                            # models.db.session.add(barcode)
                            # models.db.session.commit()
                            # print(f"Detected barcode: {barcode_text}")
                emit_update_barcodes()

        except Exception as e:
            print(f"Error reading barcodes: {e}")

        # # Распознаём штрихкоды
        # barcodes = decode(img)
        # results = []
        #
        # for barcode in barcodes:
        #     barcode_data = barcode.data.decode("utf-8")
        #     barcode_type = barcode.type
        #     results.append({
        #         "data": barcode_data,
        #         "type": barcode_type,
        #         "rect": {
        #             "left": barcode.rect.left,
        #             "top": barcode.rect.top,
        #             "width": barcode.rect.width,
        #             "height": barcode.rect.height
        #         } if hasattr(barcode, 'rect') else None
        #     })
        #
        # # Отправляем результаты обратно клиенту
        # emit('barcodes_found', {
        #     'barcodes': results,
        #     'timestamp': data.get('timestamp', '')
        # })

    except Exception as e:
        print(f"Ошибка обработки кадра: {str(e)}")
        #emit('processing_error', {'error': str(e)})


def emit_update_barcodes():
    with app_context():
        emit('update_barcodes', {
            'barcodes': sorted(detected_barcodes),
            'box_number': current_box.box_number if current_box else None,
            'is_sealed': current_box.is_sealed if current_box else False
        })


if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', ssl_context=('cert.pem', 'key.pem'))
