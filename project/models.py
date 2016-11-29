from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import hashlib
from Crypto.PublicKey import RSA
from utils import create_cloudsql_engine


WORD_HASH_SALT = os.environ.get('WORD_HASH_SALT')
WORD_PRIVATE_KEY = os.environ.get('WORD_PRIVATE_KEY')


Base = declarative_base()
Session = sessionmaker(bind=create_cloudsql_engine())
session = Session()


keypair = RSA.importKey(WORD_PRIVATE_KEY)


class Word(Base):
    """A record of a word found on a web page, with the number of times
    it was found across all searches.
    The word is encrypted, and stored with a salted hash as its primary key.
    """
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
        """Given a word, return the encrypted version.
        """
        return keypair.encrypt(text.encode('UTF'), 32)[0]

    @property
    def decrypted_text(self):
        """Returns the decrypted version of this word.
        """
        return keypair.decrypt(self.encrypted_text)

    def __repr__(self):
        return "<Word {}>".format(self.hash_id)


def save_words(common_tuples):
    """Given a list of two tuples, saves the words to the database.
    Each tuple is in the form (text, frequency).
    """
    for word_string, frequency in common_tuples:
        hash_id = Word.make_hash_id(word_string)
        # TODO this could be optimised to do bulk updates / inserts
        word = session.query(Word).filter_by(hash_id=hash_id).first()
        if word:
            word.frequency += frequency
        else:
            session.add(Word(hash_id=hash_id,
                             encrypted_text=Word.encrypt_text(word_string),
                             frequency=frequency))
        session.commit()
