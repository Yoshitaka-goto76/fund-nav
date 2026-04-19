#!/usr/bin/env python3
"""
投資信託 基準価額スクレイパー
GitHub Actions で毎日実行し nav.json に出力する
"""
import json
import time
import requests
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://www.am.mufg.jp/',
}

# ============================================================
# ファンド設定
# api: 'mufg' = 三菱UFJアセットマネジメントAPI
#       None   = 未対応（nav=null で出力）
# fund_cd: 三菱UFJアセット内部コード（fund_searchで検索して確認）
# ============================================================
FUNDS = [
    {
        'name': 'eMAXIS Slim 全世界株式',
        'code': '0331418A',
        'api': 'mufg',
        'fund_cd': '253425',
    },
    {
        'name': 'eMAXIS Slim 米国株式(S&P500)',
        'code': '0331120A',
        'api': 'mufg',
        'fund_cd': '253266',
    },
    {
        'name': '年金プラス',
        'code': '2931137C',
        'api': None,
        'fund_cd': None,
    },
    {
        'name': 'ロボプロ',
        'code': '2931237C',
        'api': None,
        'fund_cd': None,
    },
    {
        'name': '宇宙関連株式ファンド（ヘッジなし）',
        'code': '02312213',
        'api': None,
        'fund_cd': None,
    },
]


def fetch_mufg_nav(fund_cd: str):
    url = f'https://www.am.mufg.jp/mukamapi/fund_details/?fund_cd={fund_cd}'
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        if data.get('result', {}).get('status') != 200:
            print(f'  API error: {data.get("result")}')
            return None
        ds = data.get('datasets', {})
        if not ds:
            return None
        date_raw = str(ds.get('cfm_base_date', ''))
        date_str = f'{date_raw[:4]}/{date_raw[4:6]}/{date_raw[6:]}' if len(date_raw) == 8 else date_raw
        return {
            'nav':    ds.get('cfm_base_price'),
            'change': ds.get('cfm_price_changes'),
            'pct':    None,
            'date':   date_str,
        }
    except Exception as e:
        print(f'  fetch error: {e}')
        return None


def main():
    now_jst = datetime.now(JST).isoformat()
    results = {'updated': now_jst, 'funds': []}

    for fund in FUNDS:
        entry = {
            'name':   fund['name'],
            'code':   fund['code'],
            'nav':    None,
            'change': None,
            'pct':    None,
            'date':   None,
        }

        print(f'Fetching: {fund["name"]} ...')

        if fund['api'] == 'mufg' and fund['fund_cd']:
            data = fetch_mufg_nav(fund['fund_cd'])
            if data:
                entry.update(data)
                print(f'  OK: {data["nav"]}円 ({data["change"]:+}円) {data["date"]}')
            else:
                print(f'  FAILED')
        else:
            print(f'  Skipped (api not configured)')

        results['funds'].append(entry)
        time.sleep(1)

    with open('nav.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\nDone. Saved nav.json')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
