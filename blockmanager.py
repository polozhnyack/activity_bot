from datetime import datetime, timedelta
from typing import Optional


class BlockManager:
    def __init__(self):
        self.blocks = {}  # user_id -> blocked_until
        self.attempts = {}  # user_id -> attempts_count
    
    def is_blocked(self, user_id: int) -> bool:
        if user_id not in self.blocks:
            return False
        
        if datetime.now() > self.blocks[user_id]:
            del self.blocks[user_id]
            del self.attempts[user_id]  # очищаем и попытки при разблокировке
            return False
        
        return True
    
    def block_user(self, user_id: int, hours: int = 24):
        self.blocks[user_id] = datetime.now() + timedelta(hours=hours)
    
    def get_block_time(self, user_id: int) -> Optional[datetime]:
        return self.blocks.get(user_id)
    
    def increment_attempts(self, user_id: int) -> int:
        """Увеличивает счетчик попыток и возвращает новое значение"""
        if user_id not in self.attempts:
            self.attempts[user_id] = 0
        self.attempts[user_id] += 1
        return self.attempts[user_id]
    
    def get_attempts(self, user_id: int) -> int:
        """Возвращает текущее количество попыток"""
        return self.attempts.get(user_id, 0)
    
    def reset_attempts(self, user_id: int):
        """Сбрасывает счетчик попыток"""
        if user_id in self.attempts:
            del self.attempts[user_id]