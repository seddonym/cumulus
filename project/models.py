#!python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Word(Base):
    __tablename__ = 'words'
    hash_id = Column(String(56), primary_key=True)
    encrypted_text = Column(String(256), nullable=False)
    frequency = Column(Integer, nullable=False)

    def __repr__(self):
        return "<Word {}>".format(self.hash_id)
