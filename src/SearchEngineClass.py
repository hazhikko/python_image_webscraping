# coding: utf-8
import urllib, pprint, json, time, sys
import SearchBaseClass
from bs4 import BeautifulSoup
from common.CommonConst import PROXIES, CONNECT_TIMEOUT, SEARCH_URL, UA, IMG_EXT, DATA_DIR
from common.CommonConst import INFO_MESSAGE, ERROR_MESSAGE

class SearchGoogleClass(SearchBaseClass.ImageClass):
    def query_gen(self, site, keyword):
        """検索用のURLを作成する
        
        Arguments:
            site {str} -- 検索サイト
            keyword {str} -- 検索キーワード
        
        Yields:
            str -- 作成したURL
        """
        # 'q':keyword,      検索キーワード
        # 'tbm':'isch',     検索種類(isch=画像検索)
        # 'tbs':'sur:fc',   ライセンス指定(sur:fc=再使用が許可された画像)
        # 'ijn':str(page)   指定したページを表示する
        while True:
            params = urllib.parse.urlencode({
                'q':keyword,
                'tbm':'isch',
                # 'tbs':'sur:fc',
                'ijn':str(self.page)})
            yield SEARCH_URL[site] + '?' + params
            self.page += 1
            time.sleep(1)
    
    def get_url_list(self, query_gen):
        """検索エンジンからURLのリストを取得する
        
        Arguments:
            query_gen {object} -- query_genで作成したジェネレータ
        
        Retruens:
            list -- urlのリスト
        """
        html = self.session.get(next(query_gen), proxies = PROXIES, timeout = CONNECT_TIMEOUT).text
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select('.rg_meta.notranslate')
        jsons = [json.loads(e.get_text()) for e in elements]
        return [js['ou'] for js in jsons]

class SearchBingClass(SearchBaseClass.ImageClass):
    def __init__(self):
        super(SearchBingClass, self).__init__()
        self.item_count = 0
        self.item = 0

    def query_gen(self, site, keyword):
        """検索用のURLを作成する
        
        Arguments:
            site {str} -- 検索サイト
            keyword {str} -- 検索キーワード
        
        Yields:
            str -- 作成したURL
        """
        # 'q':keyword,                      検索キーワード
        # 'qft':'+filterui:license-L1',     ライセンス指定(license-L1=パブリックドメイン)
        # 'first':str(item)                 ページの先頭に表示する画像を指定する
        while True:
            params = urllib.parse.urlencode({
                'q':keyword,
                # 'qft':'+filterui:license-L1',
                'first':str(self.item)})
            yield SEARCH_URL[site] + '?' + params
            self.item += len(self.result['download']) + len(self.result['download_error']) + len(self.result['download_skip']) + 1
            time.sleep(1)
    
    def get_url_list(self, query_gen):
        """検索エンジンからURLのリストを取得する
        
        Arguments:
            query_gen {object} -- query_genで作成したジェネレータ
        
        Retruens:
            list -- urlのリスト
        """
        html = self.session.get(next(query_gen), proxies = PROXIES, timeout = CONNECT_TIMEOUT).text
        soup = BeautifulSoup(html, 'lxml')
        elements = soup.select('a.iusc')
        jsons = [json.loads(e['m']) for e in elements]
        return [js['murl'] for js in jsons]


if __name__ == '__main__':
    # パラメータ：検索サイト(google or bing), 検索キーワード, 取得枚数
    if len(sys.argv) != 4:
        print(ERROR_MESSAGE['common_err_007'])
        sys.exit()
    else:
        site = sys.argv[1]
        keyword = sys.argv[2]
        num = sys.argv[3]
        if site == 'bing':
            GetImages = SearchBingClass()
        else:
            GetImages = SearchGoogleClass()
        result = GetImages.search(site, keyword, maximum=int(num))
        pprint.pprint(result)