from sqlalchemy.orm import Session
import models


def get_data(db: Session, chat_id: str):
    results = db.query(models.Data).filter(models.Data.chat_id == chat_id).all()
    return [i.token for i in results]


def get_active(db: Session, chat_id: str):
    results = db.query(models.Data).filter(models.Data.chat_id == chat_id, models.Data.active == True).first()
    return results.token


def get_chat_id(db: Session, token: str):
    results = db.query(models.Data).filter(models.Data.token == token, models.Data.active == True).all()
    return [i.chat_id for i in results]


def update_active(db: Session, chat_id: str, token: str):
    db.query(models.Data).filter_by(chat_id=chat_id, active=True).update({'active': False})
    db.query(models.Data).filter_by(chat_id=chat_id, token=token).update({'active': True})
    db.commit()


def create_data(db: Session, chat_id: str, token: str):
    db_data = models.Data(**{"chat_id": chat_id, "token": token, "active": False})
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data


def delete_data(db: Session, chat_id: str):
    db.query(models.Data).filter(models.Data.chat_id == chat_id, models.Data.active == True).delete()
    db.commit()
