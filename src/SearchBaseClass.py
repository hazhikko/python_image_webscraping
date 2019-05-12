# coding: utf-8
import os, os.path, sys, json, glob, urllib, urllib.robotparser, pprint, glob, hashlib, shutil, time
import requests
from requests.exceptions import Timeout
from bs4 import BeautifulSoup
from common.CommonConst import PROXIES, CONNECT_TIMEOUT, SEARCH_URL, UA, IMG_EXT, DATA_DIR, DISK_FREE_REFERENCE_VALUE
from common.CommonConst import INFO_MESSAGE, ERROR_MESSAGE

class ImageClass:
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update(UA)
        self.site = ''
        self.keyword = ''
        self.maximum = 0
        self.require = 0
        self.page = 0
        self.result = {}
        self.retry_flg = False
    
    def search(self, site, keyword, maximum):
        """画像の検索とダウンロード処理を行う
        
        Arguments:
            site {str} -- 検索サイト
            keyword {str} -- 検索キーワード
            maximum {int} -- 取得したい画像の数
        
        Returns:
            object -- ダウンロード結果
        """
        self.site = site
        self.keyword = keyword
        self.maximum = self.require = maximum
        if site not in SEARCH_URL:
            print(ERROR_MESSAGE['common_err_004'])
            site = 'google'
        while True:
            query = self.query_gen(site, keyword)
            url_list = self.image_search(query, maximum)
            self.download_file(keyword, url_list)
            if not self.retry_flg:
                break
        print(INFO_MESSAGE['common_info_004'])
        print(INFO_MESSAGE['common_info_006'].format(len(self.result['download']) if 'download' in self.result else 0))
        print(INFO_MESSAGE['common_info_007'].format(len(self.result['download_error']) if 'download_error' in self.result else 0))
        print(INFO_MESSAGE['common_info_008'].format(len(self.result['download_skip']) if 'download_skip' in self.result else 0))
        return self.result
    
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
            self.page += 1
            yield SEARCH_URL[site] + '?' + params
            time.sleep(1)
    
    def image_search(self, query_gen, maximum):
        """検索サイトで画像を検索し、画像のURLを収集する
        
        Arguments:
            query_gen {object} -- query_genで作成したジェネレータ
            maximum {int} -- 取得したい画像の数
        
        Returns:
            list -- 画像URLのリスト/検索結果が0件だった場合は空List
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
            if not len(imageURLs):
                return []
            else:
                # URLの形式をチェックする
                delete_list = []
                for i, url in enumerate(imageURLs):
                    # パラメータがついている場合は削除する
                    split_url = url.split('?')[0]
                    ext = os.path.splitext(split_url)[1][1:]
                    if any(ext == s for s in IMG_EXT):
                        imageURLs[i] = split_url
                    else:
                        # 画像ではない場合リストから削除する
                        delete_list.append(url)
                if len(delete_list):
                    [imageURLs.remove(del_url) for del_url in delete_list]
                if len(imageURLs) > self.require - total:
                    result += imageURLs
                    break
                else:
                    result += imageURLs
                    total += len(imageURLs)
        print(INFO_MESSAGE['common_info_002'])
        return result
    
    def check_disk_usage(self, path):
        """ディスクの空き/使用容量の割合を返却する
        
        Arguments:
            path {str} -- チェック対象のディスクのパス
        
        Returns:
            list {int} -- 空き率, 使用率
        """
        disk_total = int(shutil.disk_usage(path).total / 1024 /1024)
        disk_free = int(shutil.disk_usage(path).free / 1024 /1024)
        free_percentage = int(disk_free / disk_total * 100)
        used_percentage = 100 - free_percentage
        return [free_percentage, used_percentage]

    def check_redundant_image(self, tmp_image, save_dir):
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
    
    def check_access_permissions(self, url):
        """robots.txtを読んでアクセス権限を返却する
        
        Arguments:
            url {str} -- チェック対象のURL
        
        Returns:
            boolean -- 許可：True/不可：False
        """
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri = urllib.parse.urlparse(url))
        try:
            robot_url = domain + 'robots.txt'
            proxy = urllib.request.ProxyHandler(PROXIES)
            opener = urllib.request.build_opener(proxy)
            urllib.request.install_opener(opener)
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robot_url)
            rp.read()
            return rp.can_fetch('*', url)
        except:
            return False
    
    def check_download_continue(self, url_list, save_dir):
        """ダウンロードを継続するかチェックする
        
        Arguments:
            url_list {list} -- 画像URLのリスト
            save_dir {str} -- 画像の保存ディレクトリパス
        
        Returns:
            boolean -- 継続：True/終了：False
        """
        # 取得する画像がない
        if not len(url_list):
            print(INFO_MESSAGE['common_info_010'])
            return False
        # ダウンロード成功数が取得枚数に到達
        if 'download' in self.result and len(self.result['download']) >= self.maximum:
            return False
        # 保存先のディスクの空き容量が基準値以下
        if self.check_disk_usage(save_dir)[0] < DISK_FREE_REFERENCE_VALUE:
            print(INFO_MESSAGE['common_info_005'].format(DISK_FREE_REFERENCE_VALUE))
            return False
        return True
    
    def download_file(self, keyword, url_list):
        """リスト内の画像をローカルに保存する
        
        Arguments:
            keyword {str} -- [description]
            url_list {list} -- [description]
        
        Raises:
            ValueError -- HTTP statusが200以外だった場合
            TypeError -- Content-Typeが画像以外だった場合
        
        Returns:
            dict -- ダウンロードの結果
        """
        print(INFO_MESSAGE['common_info_003'])
        keyword = keyword.replace(' ', '_').replace('　', '_')
        save_dir = DATA_DIR + '/' + keyword
        tmp_dir = DATA_DIR + '/' + 'tmp'
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(save_dir, exist_ok=True)
        os.makedirs(tmp_dir, exist_ok=True)

        domain = ''
        for i, url in enumerate(url_list):
            # 処理を継続するかチェックする
            if not self.check_download_continue(url_list, save_dir):
                break
            # スクレイピングが許可されているかチェック
            if not self.check_access_permissions(url):
                print(ERROR_MESSAGE['common_err_008'])
                self.result.setdefault('download_error', []).append(url)
                continue
            # ファイル名用の連番を取得
            num = self.get_file_num(save_dir)
            # ファイル名とパスを作成
            fName = os.path.basename(url)
            fPath = save_dir + '/' + str(num).zfill(5) + os.path.splitext(fName)[1]
            tmpPath = tmp_dir + '/' + str(num).zfill(5) + os.path.splitext(fName)[1]
            try:
                # 同じドメインからURLを取得する場合はスリープ
                if domain == '{uri.scheme}://{uri.netloc}/'.format(uri = urllib.parse.urlparse(url)):
                    time.sleep(1)
                domain = '{uri.scheme}://{uri.netloc}/'.format(uri = urllib.parse.urlparse(url))
                # サイトからデータ取得
                response = self.session.get(url, proxies = PROXIES, timeout = CONNECT_TIMEOUT)
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
                skip_file = self.check_redundant_image(tmpPath, save_dir)
                if skip_file != '':
                    print(ERROR_MESSAGE['common_err_002'])
                    self.result.setdefault('download_skip', []).append(skip_file)
                    continue
                self.result.setdefault('download', []).append(fPath)
            except requests.exceptions.ConnectTimeout:
                print(ERROR_MESSAGE['common_err_003'])
                self.result.setdefault('download_error', []).append(url)
                continue
            except ValueError:
                print(ERROR_MESSAGE['common_err_005'])
                self.result.setdefault('download_error', []).append(url)
                continue
            except TypeError:
                print(ERROR_MESSAGE['common_err_001'])
                self.result.setdefault('download_error', []).append(url)
                continue
            except:
                print(ERROR_MESSAGE['common_err_999'])
                self.result.setdefault('download_error', []).append(url)

                import traceback
                traceback.print_exc()
                continue
        # 取得する画像がない場合は終了する
        if not self.check_download_continue(url_list, save_dir):
            self.retry_flg = False
        # ダウンロード成功数が足りなければリトライする
        elif 'download' in self.result and len(self.result['download']) < self.maximum:
            print(INFO_MESSAGE['common_info_009'])
            self.retry_flg = True
            self.require = self.maximum - len(self.result['download'])
            # self.search(self.site, self.keyword, self.maximum)
        elif 'download' not in self.result:
            self.retry_flg = True
            # self.search(self.site, self.keyword, self.maximum)
        else:
            self.retry_flg = False
        return self.result


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
