from tinydb import TinyDB, Query

class DB:
    def __init__(self):
        self.db =  TinyDB("db.json")

    def insert_send_history(self, uuid):
        table = self.db.table("send_history")
        table.insert({"uuid": uuid})

    def is_sent(self, uuid):
        table = self.db.table("send_history")
        qry = Query()
        return table.contains(qry.uuid == uuid)
