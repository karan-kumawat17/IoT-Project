from app import db
from datetime import datetime


class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    pressure = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"SensorData(Device: '{self.device_id}', '{self.temperature}C', '{self.humidity}%', '{self.pressure}hPa', '{self.date_created}')"


class ImageData(db.Model):
    __tablename__ = 'image_data'
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    filepath = db.Column(db.String(255), nullable=False)
    image_binary = db.Column(db.LargeBinary, nullable=False)
    sensor_data_id = db.Column(db.Integer, db.ForeignKey('sensor_data.id'), nullable=True)
    is_fire_hazard = db.Column(db.Boolean, default=False)
    # Define relationship with SensorData
    sensor_data = db.relationship('SensorData', backref=db.backref('images', lazy=True))

    def __repr__(self):
        return f"ImageData(Device: '{self.device_id}', '{self.filename}', '{self.timestamp.isoformat()}', '{self.filepath}', '{self.sensor_data_id}')"
    

