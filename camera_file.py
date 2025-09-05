import time
import cv2
from base_camera import BaseCamera


class Camera(BaseCamera):
    counter = 0
    """An emulated camera implementation that streams a repeated sequence of
    files 1.jpg, 2.jpg and 3.jpg at a rate of one frame per second."""
    imgs = [cv2.imread(f + '.jpg') for f in ['1', '2', '3']]

    @classmethod
    def frames(cls):
        while True:
            idx = cls.counter % 3
            cls.counter += 1
            #print(idx)
            yield Camera.imgs[idx]
            time.sleep(1)