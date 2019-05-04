# python_image_webscraping
## 機能概要
Google or Bingから画像を収集する
* 検索サイトで画像検索を行い、取得した画像をローカルにダウンロードする
* ダウンロードした画像がすでに保存されている画像と同じものだった場合は保存しない
    * 一度ダウンロードしてから画像の比較を行うため、通信料の削減にはならない
## 実行環境
Python 3.7で動作確認済み
### 追加パッケージ
* requests
* beautifulsoup4
* lxml
### ファイルの配置
Anacondaで仮想環境を作成した場合

/Anaconda3/envs/【作成した環境名】/[src](https://github.com/hazhikko/python_image_webscraping/tree/master/src)/  
/Anaconda3/envs/【作成した環境名】/Lib/site-packages/[importpath.pth](https://github.com/hazhikko/python_image_webscraping/blob/master/Lib/site-packages/importpath.pth)
### ファイルの修正
#### [importpath.pth](https://github.com/hazhikko/python_image_webscraping/blob/master/Lib/site-packages/importpath.pth)
自分の環境に合わせてパスを書き換える
#### プロキシ
プロキシの設定が必要な場合は[CommonConst.py](https://github.com/hazhikko/python_image_webscraping/blob/master/src/common/CommonConst.py)の【PROXIES】を変更する
#### 画像の保存ディレクトリ
変更する場合は[CommonConst.py](https://github.com/hazhikko/python_image_webscraping/blob/master/src/common/CommonConst.py)の【DATA_DIR】を変更する
## 使い方
パラメータは4つ
1. 実行ファイル名:SearchEngineClass.pyを指定
2. 検索サイト:google or bingを指定
3. 検索キーワード:画像検索で使用するキーワードを指定
4. 取得枚数:ダウンロードする枚数を指定
### 例
`python SearchEngineClass.py google 猫 10`
→Google画像検索で猫を検索し、画像を10枚ダウンロードする

`python SearchEngineClass.py bing '猫 黒い' 100`
→2つのキーワードを使用し、bingから画像を100枚ダウンロードする
### 注意
検索時にライセンスのフィルターをかけているため、版権系の画像はほとんどヒットしないと思われる
フィルターを無効化する場合は、【def query_gen】の以下をコメントアウトする
```
# Googleの場合
while True:
    params = urllib.parse.urlencode({
        'q':keyword,
        'tbm':'isch',
        # 'tbs':'sur:fc',
        'ijn':str(page)})
    yield SEARCH_URL[site] + '?' + params
    page += 1
# Bingの場合
while True:
    params = urllib.parse.urlencode({
        'q':keyword,
        # 'qft':'+filterui:license-L1',
        'first':str(item)})
    yield SEARCH_URL[site] + '?' + params
    time.sleep(1)
    item += self.item_count
```

