# coding: utf-8
import os, os.path, sys, json, glob, urllib, pprint, glob, hashlib, shutil
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
from common.CommonConst import PROXIES, CONNECT_TIMEOUT, SEARCH_URL, UA, IMG_EXT, DATA_DIR
from common.CommonConst import INFO_MESSAGE, ERROR_MESSAGE

class ImageClass:
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(UA)
    
    def search(self, site, keyword, maximum):
        """画像の検索とダウンロード処理を行う
        
        Arguments:
            site {str} -- 検索サイト
            keyword {str} -- 検索キーワード
            maximum {int} -- 取得したい画像の数
        
        Returns:
            object -- ダウンロード結果
        """
        if site not in SEARCH_URL:
            print(ERROR_MESSAGE['common_err_004'])
            site = 'google'
        query = self.query_gen(site, keyword)
        url_list = self.image_search(query, maximum)
        return self.download_file(keyword, url_list)
    
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
        page = 0
        while True:
            params = urllib.parse.urlencode({
                'q':keyword,
                'tbm':'isch',
                'tbs':'sur:fc',
                'ijn':str(page)})
            yield SEARCH_URL[site] + '?' + params
            page += 1
    
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
            elements = soup.select('.rg_meta.notranslate')
            jsons = [json.loads(e.get_text()) for e in elements]
            imageURLs = [js['ou'] for js in jsons]

            # 取得枚数がmaximumに達するまでクエリを再作成して取得を繰り返す
            # 検索結果が0件だった場合は処理を終了する
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
    
    def redundant_image_check(self, tmp_image, save_dir):
        """ダウンロードした画像と同じ画像があるかチェックする
        
        Arguments:
            tmp_image {str} -- 一時ディレクトリにダウンロードした画像のパス
            save_dir {str} -- 重複チェックを行うディレクトリのパス
        
        Returns:
            str -- 重複画像が保存されているパス/該当がなければ空文字
        """
        flg = True
        redundant_image_path = ''
        target = open(tmp_image, 'rb').read()
        target_md5 = hashlib.md5(target).hexdigest()
        files = glob.glob(save_dir + '/*' + os.path.splitext(tmp_image)[1])
        # それぞれの画像のhash値を比較する
        # 重複した場合は画像を削除する
        if len(files) > 0:
            for file in files:
                with open(file, 'rb') as image:
                    image_data = image.read()
                    image_md5 = hashlib.md5(image_data).hexdigest()
                    if image_md5 == target_md5:
                        flg = False
                        redundant_image_path = file.replace('\\', '/')
                        break
        if flg:
            shutil.move(tmp_image, save_dir)
        else:
            os.remove(tmp_image)
        return redundant_image_path
    
    def get_file_num(self, save_dir):
        """画像の保存先内で一番大きい連番ファイル名を取得し、次の連番を返す
        
        Arguments:
            save_dir {str} -- 画像の保存先ディレクトリのPath
        
        Returns:
            int -- 次に使用する連番
        """
        files = glob.glob(save_dir + '/*')
        if len(files) > 0:
            last_file = os.path.basename(files[-1].replace('\\', '/'))
            return int(os.path.splitext(last_file)[0]) + 1
        else:
            return 1
    
    def download_file(self, keyword, url_list):
        """リスト内の画像をローカルに保存する
        
        Arguments:
            keyword {str} -- [description]
            url_list {list} -- [description]
        Raises:


        Returns:
            dict -- ダウンロードの結果
        """
        print(INFO_MESSAGE['common_info_003'])
        save_dir = DATA_DIR + '/' + keyword
        tmp_dir = DATA_DIR + '/' + 'tmp'
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(save_dir, exist_ok=True)
        os.makedirs(tmp_dir, exist_ok=True)

        result = {}
        for i in range(len(url_list)):
            # ファイル名用の連番を取得
            num = self.get_file_num(save_dir)
            # ファイル名とパスを作成
            fName = os.path.basename(url_list[i])
            fPath = save_dir + '/' + str(num).zfill(5) + os.path.splitext(fName)[1]
            tmpPath = tmp_dir + '/' + str(num).zfill(5) + os.path.splitext(fName)[1]
            # 画像の拡張子を取得
            # ext = os.path.splitext(fName)[1][1:]
            # 画像のみダウンロード
            if os.path.splitext(fName)[1][1:] not in IMG_EXT:
                print(ERROR_MESSAGE['common_err_001'])
                result.setdefault('download_error', []).append(url_list[i])
                continue
            else:
                try:
                    # サイトからデータ取得
                    response = self.session.get(url_list[i], proxies = PROXIES, timeout = CONNECT_TIMEOUT)
                    if response.status_code != 200:
                        e = ValueError("HTTP status: " + response.status_code)
                        raise e
                    
                    content_type = response.headers['content-type']
                    if 'image' not in content_type:
                        e = TypeError("Content-Type: " + content_type)
                        raise e
                    
                    # ファイルをローカルに保存
                    with open(tmpPath, mode = 'wb') as f:
                        f.write(response.content)
                    # 同じファイルがあればスキップする
                    skip_file = self.redundant_image_check(tmpPath, save_dir)
                    if skip_file != '':
                        print(ERROR_MESSAGE['common_err_002'])
                        result.setdefault('download_skip', []).append(skip_file)
                        continue
                    result.setdefault('download', []).append(fPath)
                except requests.exceptions.ConnectTimeout:
                    print(ERROR_MESSAGE['common_err_003'])
                    result.setdefault('download_error', []).append(url_list[i])
                    continue
                except ValueError:
                    print(ERROR_MESSAGE['common_err_005'])
                    result.setdefault('download_error', []).append(url_list[i])
                    continue
                except TypeError:
                    print(ERROR_MESSAGE['common_err_001'])
                    result.setdefault('download_error', []).append(url_list[i])
                    continue
                except:
                    print(ERROR_MESSAGE['common_err_999'])
                    result.setdefault('download_error', []).append(url_list[i])

                    import traceback
                    traceback.print_exc()
                    continue
        print(INFO_MESSAGE['common_info_004'])
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
        GetImages = ImageClass()
        result = GetImages.search(site, keyword, maximum=int(num))
        pprint.pprint(result)
