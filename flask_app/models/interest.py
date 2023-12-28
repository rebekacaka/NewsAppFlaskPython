from flask_app.config.mysqlconnection import MySQLConnection, connectToMySQL


class Interest:
    db_name="newsapp"
    def __init__(self,data):
        self.id=data['id']
        self.key_word=data['key_word']
        self.user_id=data['user_id']
        self.created_at=data['created_at']
        self.updated_at=data['updated_at']

    @classmethod
    def get_all_User_Interest(cls,data):
        query="select * from interests where user_id = %(user_id)s"
        results = connectToMySQL(cls.db_name).query_db(query,data)
        topics=[]
        if results:
            for topic in results:
                topics.append(cls(topic))
        return topics
    
    @classmethod
    def addInterest(cls,data):
        query = "insert into interests (key_word, user_id) values (%(key_word)s, %(user_id)s);"
        return connectToMySQL(cls.db_name).query_db(query,data)
    
    @classmethod
    def removeInterest(cls,data):
        query = "delete from interests where id = %(id)s;"
        return connectToMySQL(cls.db_name).query_db(query,data)