# coding: utf-8

import sqlite3
import ErrorClass
from common.CommonConst import INFO_MESSAGE, ERROR_MESSAGE, DB
from ErrorClass import SqlError
import pprint, os

class SqliteClass:
    def __init__(self, db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        try:
            self.connect = sqlite3.connect(db_path)
            self.cursor = self.connect.cursor()
        except sqlite3.Error as e:
            pprint.pprint(e)
            raise SqlError(ERROR_MESSAGE['common_err_006'].format(e.args[0]))
    
    def __del__(self):
        self.connect.commit()
        self.connect.close()
    
    def sql_execute(self, query, data = None):
        """SQLを実行する
        
        Arguments:
            query {str} -- 実行するquery
        
        Keyword Arguments:
            data {List} -- queryに付随するデータ
        
        Raises:
            SqlError -- SQLite実行時にエラーが発生した場合
        
        Returns:
            List -- 実行結果をLISTに変換したもの
        """
        try:
            if data is None:
                self.cursor.execute(query)
            else:
                self.cursor.execute(query, data)
            self.connect.commit()
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            pprint.pprint(e)
            raise SqlError(ERROR_MESSAGE['common_err_006'].format(e.args[0]))

class DbClass(SqliteClass):
    def __init__(self, db_path):
        super(DbClass, self).__init__(db_path)
        self.create_table()
    
    def create_table(self):
        """tableがなければ作成する
        """
        try:
            # ドメインリスト
            query = DB['ineligible_domain']['create_table']
            self.sql_execute(query)
            # ダウンロード済みリスト
            query = DB['downloaded_list']['create_table']
            self.sql_execute(query)
        except sqlite3.Error as e:
            raise SqlError(ERROR_MESSAGE['common_err_006'].format(e.args[0]))