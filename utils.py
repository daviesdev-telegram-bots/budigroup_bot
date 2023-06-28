from models import User, session

def verfiy_float(text):
    try:
        amt = float(text)
    except:
        return None
    return amt

def get_user(uid):
    user = session.query(User).get(str(uid))
    if not user:
        user = User(id=str(uid))
        session.add(user)
        session.commit()
    return user

def get_balance(user_id):
    user = session.query(User).get(str(user_id))
    return user.balance if user else 0.0