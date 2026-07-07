import sqlite3
from  datetime import datetime

class BotDatabase:
    def __init__(self, db_name="crypto_bot.db"):
        self.db_name = db_name
        self.creat_tables()

    def _connect(self):
        return sqlite3.connect(self.db_name)

    def creat_tables(self):
        conn = self._connect()
        cursor = conn.cursor()


        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coin_preference TEXT
            )
        """
        )

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS crypto_prices(
            coin_symbol TEXT PRIMARY KEY,
            price REAL,
            last_updated TEXT
            )
        """
        )
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        symbol TEXT,
                        target_price REAL,
                        condition TEXT
                    )
                """)
        conn.commit()
        conn.close()

#===============================================Price Methods

    def update_price(self, coin_symbol, price):
        conn = self._connect()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT OR REPLACE INTO crypto_prices (coin_symbol, price, last_updated)
            VALUES (?, ?, ?)
          """,
            (coin_symbol.upper(), price, now),
        )
        conn.commit()
        conn.close()

    def get_price(self, coin_symbol):
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT price, last_updated FROM crypto_prices WHERE coin_symbol = ?",
            (coin_symbol.upper(),),
        )
        result = cursor.fetchone()
        conn.close()

        if result :
            return {"price": result[0], "time": result[1]}
        return None
#==============================================================ALERTS
    def add_alerts(self, chat_id, symbol, target_price, condition):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
                    INSERT INTO alerts (chat_id, symbol, target_price, condition)
                    VALUES (?, ?, ?, ?)
                """, (chat_id, symbol.lower(), target_price, condition))
        conn.commit()
        conn.close()

    def get_all_alerts(self, ):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, chat_id, symbol, target_price, condition FROM alerts")
        rows = cursor.fetchall()
        conn.close()

        alerts_list = []

        for row in rows:
            alerts_list.append({
                "id": row[0],
                "chat_id": row[1],
                "symbol": row[2],
                "target_price": row[3],
                "condition": row[4]
            })
        return alerts_list

    def delete_alert(self, alert_id):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()










