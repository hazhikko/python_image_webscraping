# coding: utf-8

import requests
import urllib, datetime, math
from pprint import pprint
from ErrorClass import VirustotalError, SqlError
from SqliteClass import DbClass
from common.CommonConst import INFO_MESSAGE, ERROR_MESSAGE, DB, PROXIES, CONNECT_TIMEOUT, VIRUSTOTAL

class VirustotalClass:
    def __init__(self):
        self.request_limit = math.floor(60 / VIRUSTOTAL['request_limit']) + 1
        self.db = DbClass(DB['db_path'])
        self.time = datetime.datetime.now() - datetime.timedelta(seconds=self.request_limit)
    
    def virus_scan(self, session, target):
        """一連のウイルススキャン処理を実行する
        
        Arguments:
            session {object} -- requests.session
            target {str} -- check対象のURL
        
        Returns:
            boolean -- 陰性：Falue, 陽性:True
        
        Note:
            スキャン結果陰性：downloaded_listに追加
            スキャン結果陽性：ineligible_domainに追加
        """
        try:
            scan_res = self.scan(session, target)
            report_res = self.get_report(session, scan_res['scan_id'])
            # ウイルス陽性が2未満であればOK
            if report_res['positives'] < 2:
                # チェック済みとしてリストに追加する
                query = DB['downloaded_list']['insert']
                data = (target, 0, DB['date'].format(datetime.datetime.now()))
                self.db.sql_execute(query, data=data)
                print(INFO_MESSAGE['common_info_013'].format(target, '陰性'))
                return False
            else:
                # ウイルス陽性だった場合はドメインリストに追加する
                domain = '{uri.scheme}://{uri.netloc}/'.format(uri = urllib.parse.urlparse(target))
                query = '''select count(domain) from ineligible_domain where domain='{0}' and category={1};'''.format(domain, 0)
                if self.db.sql_execute(query)[0][0] == 0:
                    query = DB['ineligible_domain']['insert']
                    data = (domain, 0, DB['date'].format(datetime.datetime.now()))
                    self.db.sql_execute(query, data=data)
                    print(INFO_MESSAGE['common_info_013'].format(target, '陽性'))
                return True
        except SqlError:
            return True
        except VirustotalError:
            # スキャンに失敗した場合は陽性として返す
            return True
    
    def scan(self, session, target):
        """スキャンを実行する
        
        Arguments:
            session {object} -- requests.session
            target {str} -- check対象のURL
        
        Raises:
            ValueError -- HTTP statusが200以外だった場合
            VirustotalError -- res['response_code']が1以外だった場合
        
        Returns:
            dic -- スキャン実行の返却値
        """
        self.wait()
        params = {
            'apikey':VIRUSTOTAL['apikey'],
            'url':target
        }
        res = requests.post(VIRUSTOTAL['url']['scan'], proxies = PROXIES, timeout = CONNECT_TIMEOUT, data=params)
        if res.status_code != 200:
            raise ValueError("HTTP status: " + res.status_code)
        res = res.json()
        if res['response_code'] == 1:
            return res
        else:
            raise VirustotalError(ERROR_MESSAGE['common_err_009'].format(res['verbose_msg']))
    
    def get_report(self, session, scan_id):
        """スキャン結果を取得する
        
        Arguments:
            session {object} -- requests.session
            scan_id {str} -- scanで取得したscan_id
        
        Raises:
            ValueError -- HTTP statusが200以外だった場合
            VirustotalError -- res['response_code']が1以外だった場合
        
        Returns:
            dic -- レポート取得の返却値
        """
        self.wait()
        params = {
            'apikey':VIRUSTOTAL['apikey'],
            'resource':scan_id
        }
        res = session.post(VIRUSTOTAL['url']['report'], proxies = PROXIES, timeout = CONNECT_TIMEOUT, data=params)
        if res.status_code != 200:
            raise ValueError("HTTP status: " + res.status_code)
        res = res.json()
        if res['response_code'] == 1:
            return res
        elif res ['response_code'] == -2:
            # レポートの作成が終わっていなかった場合は再取得する
            self.get_report(session, scan_id)
        else:
            raise VirustotalError(ERROR_MESSAGE['common_err_009'].format(res['verbose_msg']))
    
    def wait(self):
        """APIのリクエスト上限を超えないよう時間制限をかける
        """
        while True:
            if self.time < datetime.datetime.now():
                self.time = datetime.datetime.now() + datetime.timedelta(seconds=self.request_limit)
                break