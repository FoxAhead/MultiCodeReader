from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


class Box(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    box_number = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    is_sealed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    barcodes = db.relationship('Barcode', backref='box', lazy=True)


class Barcode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=False)
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    box_id = db.Column(db.Integer, db.ForeignKey('box.id'), nullable=False)

    # Уникальное сочетание кода и коробки
    __table_args__ = (db.UniqueConstraint('code', 'box_id', name='_code_box_uc'),)
