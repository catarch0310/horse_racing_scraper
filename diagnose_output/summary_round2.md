# Diagnose Round 2: Bypass Attempts

## Cloudscraper Attempts

### punters_au
- Method: cloudscraper
- Status: 202
- HTML length: 2101

### racenet_news
- Method: cloudscraper
- Status: 200
- HTML length: 257486
- ✅ **SUCCESS** — saved sample
- News-link references in HTML: 10


## Header Variant Attempts

### punters_au
- Header variant attempts:
  - Variant 1: — status 403, 919 chars
  - Variant 2: — status 403, 919 chars

### racenet_news
- Header variant attempts:
  - Variant 1: — status 403, 919 chars
  - Variant 2: — status 403, 919 chars


## racing.com SPA Analysis

### racing_com
- Status: 200
- HTML length: 88735
- JSON patterns found:
  - `__NEXT_DATA__`: 1
  - `__NEXT_DATA___keys`: ['props', 'page', 'query', 'buildId', 'assetPrefix', 'isFallback', 'isExperimentalCompile', 'gsp', 'locale', 'locales', 'defaultLocale', 'scriptLoader']
- Possible API endpoints:
  - `"https://dxp-cdn.racing.com/api/public/content/3a6fd350779340e885e5e9f663246396?v=5d2bc8e4"`
  - `"https://dxp-cdn.racing.com/api/public/content/rdc_generic12-605502.webp?v=1702b880"`
  - `"https://rmpl-p-001.sitecorecontenthub.cloud/api/gateway/92564/thumbnail"`
  - `"https://dxp-cdn.racing.com/api/public/content/IR-MAY26-FA-8675222.pdf?v=85faceb1"`
  - `"https://rmpl-p-001.sitecorecontenthub.cloud/api/gateway/836331/thumbnail"`
  - `"https://dxp-cdn.racing.com/api/public/content/rdc_generic5-346370.webp?v=a1365bdc"`
  - `"https://dxp-cdn.racing.com/api/public/content/Google-Play-Store-Badge-851581.svg?v=24c847f1"`
  - `"https://dxp-cdn.racing.com/api/public/content/rdc_generic4-346367.webp?v=a0ca10b9"`
  - `"https://rmpl-p-001.sitecorecontenthub.cloud/api/gateway/2910735/thumbnail"`
  - `"https://dxp-cdn.racing.com/api/public/content/163f7ff6f0f64b37a4fb6fe28b9296e7?v=ab271e58"`

