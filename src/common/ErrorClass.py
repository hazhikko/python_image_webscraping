# coding: utf-8

class CommonError(Exception):
    """すべてのエラーを拾うためのクラス
    """

class SqlError(CommonError):
    """SQL実行時にエラーが発生した場合に投げるエラー
    """

class VirustotalError(CommonError):
    """Virustotal実行時にエラーが発生した場合に投げるエラー
    """