#!python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import hashlib
import base64
from Crypto.PublicKey import RSA
from utils import create_cloudsql_engine


WORD_HASH_SALT = os.environ.get('WORD_HASH_SALT')
WORD_PRIVATE_KEY = os.environ.get('WORD_PRIVATE_KEY')


Base = declarative_base()
Session = sessionmaker(bind=create_cloudsql_engine())
session = Session()


keypair = RSA.importKey(WORD_PRIVATE_KEY)


class Word(Base):
    __tablename__ = 'words'
    
    MAX_WORD_LENGTH = 256
    hash_id = Column(String(56), primary_key=True)
    encrypted_text = Column(String(MAX_WORD_LENGTH), nullable=False)
    frequency = Column(Integer, nullable=False)

    @classmethod
    def make_hash_id(cls, text):
        """Returns a salted hash of the given text.
        """
        return hashlib.sha224(text + WORD_HASH_SALT).hexdigest()
    
    @classmethod
    def encrypt_text(cls, text):
        #if len(text) > cls.MAX_WORD_LENGTH:
        #    raise ValueError('Could not encrypt {text} as it was above the maximum '
        #                     'word length of {length}.'.format(text=text,
        #                                                       length=cls.MAX_WORD_LENGTH))
        return keypair.encrypt(text.encode('UTF'), 32)[0]
    
    @classmethod
    def decrypt_text(cls, text):
        return keypair.decrypt(text)
    
    def __repr__(self):
        return "<Word {}>".format(self.hash_id)


def save_words(common_tuples):
    """Given a list of words, saves them to the database.
    """
    for word_string, frequency in common_tuples:
        hash_id = Word.make_hash_id(word_string)
        word = session.query(Word).filter_by(hash_id=hash_id).first()
        if word:
            word.frequency += frequency
        else:
            session.add(Word(hash_id=hash_id,
                             encrypted_text=Word.encrypt_text(word_string),
                             frequency=frequency))
        session.commit()        
        