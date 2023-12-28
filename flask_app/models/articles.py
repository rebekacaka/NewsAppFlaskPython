from flask_app.config.mysqlconnection import connectToMySQL


class Article:
    db_name="newsapp"
    def __init__(self, data):
        self.id = data['id']
        self.title = data['title']
        self.url = data['url']
        self.user_id = data['user_id']
        self.created_at = data['created_at']
        self.updated_at = data['created_at']
    
    @classmethod
    def save(cls,data):
        query = "insert into articles (title, url, user_id) values (%(title)s, %(url)s, %(user_id)s);"
        return connectToMySQL(cls.db_name).query_db(query,data)
    
    @classmethod
    def unsave(cls,data):
        query = "delete from articles where url = %(url)s and user_id = %(user_id)s"
        return connectToMySQL(cls.db_name).query_db(query,data)
    
    @classmethod
    def unsave_with_id(cls,data):
        query = "delete from articles where id = %(id)s;"
        return connectToMySQL(cls.db_name).query_db(query,data)
    
    @classmethod
    def get_all_User_Articles(cls,data):
        query="select * from articles where user_id = %(user_id)s"
        results = connectToMySQL(cls.db_name).query_db(query,data)
        articles=[]
        if results:
            for article in results:
                articles.append(cls(article))
        return articles
    
    @classmethod
    def update(cls, data):
        query = "update articles set title = %(title)s where id = %(id)s;"
        return connectToMySQL(cls.db_name).query_db(query,data)