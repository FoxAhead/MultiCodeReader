from contextlib import contextmanager
from flask import Flask, render_template, Response, jsonify
from mcr_scanner import Scanner
import models
import cv2

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///barcode_scanner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(get_frame(Scanner()), mimetype='multipart/x-mixed-replace; boundary=frame')


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


if __name__ == '__main__':
    init_database()
    app.run(debug=True, threaded=True)
