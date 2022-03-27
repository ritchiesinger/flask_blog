from time import time

from jwt import encode as jwt_encode, decode as jwt_decode, exceptions as jwt_exceptions
from passlib.apps import custom_app_context as pwd_context

from app import db, app


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    roles = db.relationship('UserRoles', backref='user', lazy=True)

    def __repr__(self):
        return f"{self.to_dict()}"

    def to_dict(self):
        user_info = {
            "id": self.id,
            "login": self.login,
            "email": self.email,
            "roles": [
                Role.query.filter_by(id=role.role_id).first().name
                if Role.query.filter_by(id=role.role_id).first() else None for role in self.roles
            ]
        }
        return user_info

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_token(self, expiration=app.config["TOKEN_EXPIRATION"]):
        token = jwt_encode({"id": self.id, "exp": time() + expiration}, app.config["SECRET_KEY"], algorithm="HS256")
        return token

    @staticmethod
    def verify_token(token):
        try:
            decoded_signature = jwt_decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt_exceptions.ExpiredSignatureError:
            return None  # valid token, but expired
        except jwt_exceptions.InvalidSignatureError:
            return None  # invalid token
        user = User.query.get(decoded_signature["id"])
        return user


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    description = db.Column(db.String(256))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }

    def __repr__(self):
        return str(self.to_dict())


class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    def __repr__(self):
        return f"<UserRole {self.user_id} {self.role_id}>"
