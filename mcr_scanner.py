from dataclasses import dataclass
import zxingcpp
import cv2
import numpy as np
# from camera_opencv import Camera
from camera_file import Camera


@dataclass
class ScannerCode:
    text: str = ''


class ScannerFrame:
    def __init__(self):
        self.image = None
        self.codes = []


class Scanner:
    def __init__(self):
        self.camera = Camera()

    def get_frame(self):
        scanner_frame = ScannerFrame()
        scanner_frame.image = self.camera.get_frame().copy()
        barcodes = zxingcpp.read_barcodes(scanner_frame.image)
        scanner_frame.codes.clear()
        for barcode in barcodes:
            self.draw_bounding_box(scanner_frame.image, barcode)
            scanner_frame.codes.append(ScannerCode(text=barcode.text))
        #print(type(scanner_frame.image), len(barcodes), scanner_frame.codes)
        return scanner_frame

    def draw_bounding_box(self, cv2_image, barcode: zxingcpp.Result):
        points = barcode.position
        pts = [(points.top_left.x, points.top_left.y),
               (points.top_right.x, points.top_right.y),
               (points.bottom_right.x, points.bottom_right.y),
               (points.bottom_left.x, points.bottom_left.y)]
        cv2.polylines(cv2_image, [np.array(pts)], True, (128, 0, 128), 5)

    # def detect_barcodes(self, image):
    #     # Открытие изображения
    #     cv2_image = cv2.imread(image_path)
    #     # Преобразование изображения в PIL
    #     cv2_image_converted = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    #     pil_image = Image.fromarray(cv2_image_converted)
    #     # Декодирование штрихкодов
    #     barcodes = zxingcpp.read_barcodes(cv2_image)
    #     for idx, barcode in enumerate(barcodes, start=1):
    #         # Рамка вокруг найденного кода
    #         draw_bounding_box(pil_image, barcode)
    #         # Номер на найденом коде
    #         draw_text_centered(pil_image, barcode, str(idx))
    #         # Описание найденного кода
    #         print(f"{idx}. Тип: {barcode.format}, Данные: {barcode.text}")
    #     if len(barcodes) > 0:
    #         # Сохранение изображения с результатом
    #         pil_image.save("output.jpg")
    #     else:
    #         print("Штрихкоды не найдены")
