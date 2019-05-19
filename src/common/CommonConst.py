# coding: utf-8
import _const
import os
import os.path

# プロキシを使用する場合は設定する
# {
#     'http': 'http://proxy.sample.com:8080',
#     'https': 'https://proxy.sample.com:8080'
# }
PROXIES = {}
# connect timeout / read timeout
CONNECT_TIMEOUT = (3.0, 3.0)
SEARCH_URL = {
    'google':'https://www.google.co.jp/search',
    'bing':'https://bing.com/images/search'
}
UA = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
IMG_EXT = ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff']
# WindowsとUnixでセパレータが異なるため、/で統一する
DATA_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../../download/image').replace('\\', '/')
DISK_FREE_REFERENCE_VALUE = 20
DB = {
    'db_path':os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../db/db.sqlite').replace('\\', '/'),
    'date':'{0:%Y%m%d%H%M%S}',
    'ineligible_domain':{
        'check_table':'''select name from sqlite_master where type='table' and name='ineligible_domain';''',
        'create_table':'''create table ineligible_domain (id int PRIMARY KEY, domain varchar, category int, insert_date varchar);''',
        'insert':'insert into ineligible_domain (domain, category, insert_date) values (?,?,?);'
    },
    'downloaded_list':{
        'check_table':'''select name from sqlite_master where type='table' and name='downloaded_list';''',
        'create_table':'''create table downloaded_list (id int PRIMARY KEY, url varchar, insert_date varchar)''',
        'insert':'insert into downloaded_list (url, insert_date) values (?,?)'
    }
}
INFO_MESSAGE = {
    'common_info_001':'画像URLの収集を開始します',
    'common_info_002':'画像URLの収集が完了しました',
    'common_info_003':'ダウンロードを開始します',
    'common_info_004':'ダウンロードが完了しました',
    'common_info_005':'ディスクの空き容量が{0}%を下回ったため、処理を終了します',
    'common_info_006':'ダウンロード成功:{0}件',
    'common_info_007':'ダウンロード失敗:{0}件',
    'common_info_008':'重複画像:{0}件',
    'common_info_009':'取得画像が足りないため、再検索します',
    'common_info_010':'検索結果が0件だったため、処理を終了します',
    'common_info_011':'ダウンロード {0}/{1}',
    'common_info_012':'処理を中断します',
}
ERROR_MESSAGE = {
    'common_err_001':'画像以外のファイルです',
    'common_err_002':'同じ画像が既に存在します',
    'common_err_003':'タイムアウトしました',
    'common_err_004':'対象外の検索サイトが指定されたため、Googleで検索を行います',
    'common_err_005':'サイトに接続できませんでした',
    'common_err_006':'SQL実行時にエラーが発生しました：{0}',
    'common_err_007':'パラメータが不足しています [検索サイト(google or bing)] [検索キーワード] [取得枚数]',
    'common_err_008':'スクレイピングが禁止されています',
    'common_err_999':'エラーが発生しました'
}