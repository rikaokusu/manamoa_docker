# リストファイルの読み込み
import accounts.list.list_black
import accounts.list.list_free_mail
import accounts.list.list_isp_mail



# 正規表現を作成する関数
def regcreate():
    subdomain_mae = "([\w]+@[\w]+?\.?("
    domain_mae = "([\w]+@("

    ato = "))"

    """ISPドメインの禁止リスト"""
    isp_domain = accounts.list.list_isp_mail.isp_domain

    """フリーメールドメインの禁止リスト"""
    free_domain = accounts.list.list_free_mail.free_domain


    """任意の禁止リスト読み込み"""
    black_domain = accounts.list.list_black.black_domain

    # リスト無いの文字列を結合させる
    isp_domain_join = '|'.join(isp_domain)
    free_domain_join  = '|'.join(free_domain)
    black_domain_join =  '|'.join(black_domain)

    # ドメイン用とサブドメイン用の正規表現を生成
    domain_reg =  domain_mae + isp_domain_join + "|" + free_domain_join + "|" + black_domain_join + ato
    subdomain_reg = subdomain_mae + isp_domain_join + "|" + free_domain_join + "|" + black_domain_join + ato

    # 正規表現を生成
    reg = domain_reg + "|" + subdomain_reg

    return reg
