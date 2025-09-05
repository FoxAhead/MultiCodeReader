from ..models import db, Box, AppConfig, BoxCode
from sqlalchemy import exc, func


class BoxService:
    @staticmethod
    def get_current_box_id():
        config = AppConfig.query.filter_by(param='current_box_id').first()
        return int(config.value) if config else None

    @staticmethod
    def get_current_box():
        box_id = BoxService.get_current_box_id()
        if not box_id:
            return None
        return Box.query.get(box_id)

    @staticmethod
    def create_new_box():
        next_box_id = db.session.query(func.max(Box.box_id)).scalar()
        next_box_id = (next_box_id or 0) + 1

        new_box = Box(box_id=next_box_id, closed=0)
        db.session.add(new_box)

        return new_box

    @staticmethod
    def close_current_box():
        current_box = BoxService.get_current_box()
        if current_box:
            current_box.closed = 1
        return current_box

    @staticmethod
    def clear_box_codes(box_id):
        BoxCode.query.filter_by(box_id=box_id).delete()

    @staticmethod
    def get_all_boxes():
        from sqlalchemy import text
        query = text("""
            SELECT b.box_id, b.closed, COUNT(bc.code) as code_count
            FROM boxes b
            LEFT JOIN box_codes bc ON b.box_id = bc.box_id
            GROUP BY b.box_id
            ORDER BY b.box_id DESC
        """)
        return db.session.execute(query)

    @staticmethod
    def get_box_codes(box_id):
        return BoxCode.query.filter_by(box_id=box_id).order_by(BoxCode.code).all()

    @staticmethod
    def get_box_code_count(box_id):
        return BoxCode.query.filter_by(box_id=box_id).count()

    @staticmethod
    def delete_box(box_id):
        box = Box.query.get(box_id)
        if box:
            db.session.delete(box)
            return True
        return False
