import requests, time, json, sys
import pandas as pd
from datetime import datetime, timezone

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'

def fetch(ticker, start, end, retries=4):
    s = requests.Session()
    s.headers.update({'User-Agent': UA})
    p1 = int(pd.Timestamp(start, tz='UTC').timestamp())
    p2 = int(pd.Timestamp(end, tz='UTC').timestamp())
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
    for attempt in range(retries):
        try:
            r = s.get(url, params={'period1': p1, 'period2': p2, 'interval': '1d', 'events': 'div,splits'}, timeout=20)
            d = r.json()
            res = d.get('chart', {}).get('result')
            if not res:
                return None, d.get('chart', {}).get('error')
            res = res[0]
            ts = res['timestamp']
            adj = res['indicators'].get('adjclose', [{}])[0].get('adjclose')
            close = res['indicators']['quote'][0].get('close')
            series = adj if adj is not None else close
            idx = pd.to_datetime(ts, unit='s', utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
            s_ser = pd.Series(series, index=idx, name=ticker).dropna()
            s_ser = s_ser[~s_ser.index.duplicated(keep='last')]
            return s_ser, None
        except Exception as e:
            time.sleep(1.5 * (attempt + 1))
            last_err = str(e)
    return None, last_err

if __name__ == '__main__':
    start, end, outcsv, *tickers = sys.argv[1:]
    cols = {}
    log = []
    for t in tickers:
        ser, err = fetch(t, start, end)
        if ser is None or ser.empty:
            log.append((t, 0, str(err)))
            print(f'{t}: FAIL {err}')
            continue
        cols[t] = ser
        log.append((t, len(ser), 'ok'))
        print(f'{t}: {len(ser)} obs, {ser.index.min().date()} -> {ser.index.max().date()}')
        time.sleep(0.4)
    df = pd.DataFrame(cols).sort_index()
    df.to_csv(outcsv)
    print('saved', outcsv, df.shape)
