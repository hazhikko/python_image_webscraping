# coding: utf-8
import urllib, pprint, json, time, sys
import SearchBaseClass
from bs4 import BeautifulSoup
from common.CommonConst import PROXIES, CONNECT_TIMEOUT, SEARCH_URL, UA, IMG_EXT, DATA_DIR
from common.CommonConst import INFO_MESSAGE, ERROR_MESSAGE

class SearchGoogleClass(SearchBaseClass.ImageClass):
    pass

class SearchBingClass(SearchBaseClass.ImageClass):
    item_count = 0

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
        item = 0
        while True:
            params = urllib.parse.urlencode({
                'q':keyword,
                'qft':'+filterui:license-L1',
                'first':str(item)})
            yield SEARCH_URL[site] + '?' + params
            time.sleep(1)
            item += self.item_count
    
    def image_search(self, query_gen, maximum):
        """検索サイトで画像を検索し、画像のURLを収集する
        
        Arguments:
            query_gen {object} -- query_genで作成したジェネレータ
            maximum {int} -- 取得したい画像の数
        
        Returns:
            list -- 画像URLのリスト
        """
        print(INFO_MESSAGE['common_info_001'])
        result = []
        total = 0
        while True:
            html = self.session.get(next(query_gen), proxies = PROXIES, timeout = CONNECT_TIMEOUT).text
            soup = BeautifulSoup(html, 'lxml')
            elements = soup.select('a.iusc')
            jsons = [json.loads(e['m']) for e in elements]
            imageURLs = [js['murl'] for js in jsons]

            self.item_count = len(imageURLs)
            if not len(imageURLs):
                print(ERROR_MESSAGE['common_err_006'])
                sys.exit()
            elif len(imageURLs) > maximum - total:
                result += imageURLs[:maximum - total]
                break
            else:
                result += imageURLs
                total += len(imageURLs)
        print(INFO_MESSAGE['common_info_002'])
        return result


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