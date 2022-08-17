from config import firebase_admin, auth
from firebase_admin._auth_utils import InvalidIdTokenError
from utils.logger import get_log

log = get_log()

def create_custom_token(uid: str, shop_id: int) -> str:
    return auth.create_custom_token(uid, {"shop_id": shop_id})

class FirebaseAuthentication:
    firebase_uid = ""
    def __init__(self, custom_token: str) -> None:
        self.custom_token = custom_token
    def verify_custom_token(self):
        try:
            decoded_token = auth.verify_id_token(self.custom_token)
            self.firebase_uid = decoded_token['uid']
            return True
        except InvalidIdTokenError as e:
            log.error(f"Token verification failed with the error: {e}")
            return False

