import datetime

def get_current_time() -> str:
    '''Return date and time used for and naming'''
    current_time: str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    return current_time