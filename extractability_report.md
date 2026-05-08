# Scraper Extractability Report

_Generated: 2026-05-08 05:51:33 UTC_
_Environment: GitHub Actions_

Tested 16 scrapers, up to 3 articles each.

## Summary

| Tier | Count | Sources |
|---|---|---|
| ✅ Tier A — Full body + quotes (use trafilatura directly) | 6 | `racing_post`, `scmp_racing`, `bloodhorse_news`, `anz_bloodstock`, `ttr_ausnz`, `smh_racing` |
| 🟡 Tier B — Partial body / lede only (try-fail with fallback) | 1 | `singtao_racing` |
| 🔴 Tier C — Headlines only / blocked | 3 | `the_straight`, `drf_news`, `equidia_racing` |
| 💀 BROKEN — Scraper module failed | 0 | _(none)_ |
| ⚠️ NO DATA — Scraper returned empty list | 6 | `punters_au`, `racing_com`, `tospo_keiba`, `netkeiba_news`, `racenet_news`, `daily_telegraph` |

---

## Detailed Results

### ✅ Tier A — Full body + quotes (use trafilatura directly)

#### `racing_post`
- Items found: 60
- Tested: 3 | Success: 3/3
- Avg body length: **4119** chars | Avg quotes: **4.7**

✅ _Inside Chester's ground chaos - a stewards' inquiry that 'went round and round i_
  - URL: <https://www.racingpost.com/news/festivals/chester-may-meeting/a-stewards-inquiry-that-went-round-and-round-in-circles-and-a-delay-of-more-than-an-hour-how-chester-ground-saga-played-out-at4Yk8V7XwTN/>
  - 6291 chars, 11 quotes
  - **Sample quotes**:
    - `Tom says the ground is dangerous,`
    - `My horse [Stratusnine] slipped turning for home [in the first race] but he was forced very wide, probably far too wide going very fast,`
    - `It's uncomfortable for jockeys when they slip but they've mowed and sanded the track and the balance of opinion was that we should race ahea`
  - Preview: _Inside Chester's ground chaos - a stewards' inquiry that 'went round and round in circles' and a delay of more than an hour Click here to add us to your Google preferred sources or find out more here …_

✅ _'If there's one horse who could have 10lb in hand it's surely him' - Tom Segal i_
  - URL: <https://www.racingpost.com/horse-racing-tips/premium-tips/pricewise/if-theres-one-horse-who-could-have-10lb-in-hand-its-surely-him-tom-segal-is-keen-on-a-chester-cup-runner-among-his-three-tips-aMHi41d3nRMy/>
  - 2282 chars, 0 quotes
  - Preview: _TippingPricewise premium 'If there's one horse who could have 10lb in hand it's surely him' - Tom Segal is keen on a Chester Cup runner among his three tips Racing Post+ tipping is our top-tier bettin…_

✅ _Plumpton forced to cancel Sunday's card after 'highly contagious' equine flu out_
  - URL: <https://www.racingpost.com/news/britain/plumpton-forced-to-cancel-sundays-card-after-highly-contagious-equine-flu-outbreak-in-nearby-livery-yard-aOENT7X5eWNb/>
  - 3786 chars, 3 quotes
  - **Sample quotes**:
    - `Equine flu is highly contagious and can spread rapidly among horses, including through the air and over a widespread distance, which is why `
    - `We have also seen a significant recent rise in the number of equine flu outbreaks across the country, in the non-thoroughbred herd. I urge t`
    - `The health and wellbeing of horses and participants remains our absolute priority, and it is believed this is the most responsible course of`
  - Preview: _Plumpton forced to cancel Sunday's card after 'highly contagious' equine flu outbreak in nearby livery yard Click here to add us to your Google preferred sources or find out more here Plumpton's meeti…_

#### `scmp_racing`
- Items found: 7
- Tested: 3 | Success: 3/3
- Avg body length: **4187** chars | Avg quotes: **4.7**

✅ _Royal Ascot needs Ka Ying Rising, but the world’s best horse does not need it_
  - URL: <https://www.scmp.com/sport/racing/article/3352779/royal-ascot-needs-ka-ying-rising-worlds-best-horse-certainly-does-not-need-it>
  - 3162 chars, 0 quotes
  - Preview: _There is a very simple fact that doesn’t seem as though European racing fans can accept – Ka Ying Rising does not need Royal Ascot, Royal Ascot needs him. Not just the world’s best sprinter any more, …_

✅ _Yiu rates Voyage Bubble ‘doubtful’ to defend Champions & Chater Cup crown_
  - URL: <https://www.scmp.com/sport/racing/article/3352721/ricky-yiu-rates-voyage-bubble-doubtful-defend-champions-chater-cup-crown>
  - 4336 chars, 4 quotes
  - **Sample quotes**:
    - `He went up to Conghua [on Wednesday morning] and they opened up the capped elbow, but doubtful to run him,`
    - `We’ll see in a week’s time, we’ll have a better picture. He’s perfect, it’s just managing the capped elbow, that’s all.`
    - `He’s still in good form – same jockey, same trip and he’s a horse on his way up. Hopefully he’ll move up to Class Two,`
  - Preview: _Trainer Ricky Yiu Poon-fai rates Voyage Bubble “doubtful” to defend his crown in the Group One Standard Chartered Champions & Chater Cup (2,400m) at Sha Tin on May 24. Yiu was keen to give the six-tim…_

✅ _Newnham continues march towards trainers’ championship, Teetan scores double_
  - URL: <https://www.scmp.com/sport/racing/article/3352668/mark-newnham-continues-march-towards-trainers-championship-karis-teetan-scores-double-sha-tin>
  - 5064 chars, 10 quotes
  - **Sample quotes**:
    - `He’s been a great contributor to the trainers’ championship, I’ll tell you,`
    - `There’s a big pack chasing so every win counts and very important at this end of the season.`
    - `Considering last year he was a winner in Class Five from gate one, I didn’t factor him winning four races this time around but he’s kept imp`
  - Preview: _Mark Newnham continued his march towards the trainers’ championship when Notthesillyone scored his fourth win for the season in the second section of the Class Four Carnation Handicap (1,200m) at Sha …_

#### `bloodhorse_news`
- Items found: 50
- Tested: 3 | Success: 3/3
- Avg body length: **2573** chars | Avg quotes: **2.7**

✅ _Young Trainer Caught in Vet's Web of Violations_
  - URL: <https://www.bloodhorse.com/horse-racing/articles/291738/young-trainer-caught-in-vets-web-of-violations>
  - 5201 chars, 6 quotes
  - **Sample quotes**:
    - `only every once in a while`
    - `Dr. McCrosky fabricated the ridgling explanation and that Childersattack was in fact a gelding at the time of the Oct. 16, 2024, sample.`
    - `covered in dirt/dust, and the bag inside the tub appeared to be full and in its original state,`
  - Preview: _Young Illinois trainer Vance Childers learned a harsh lesson recently about being too trusting of a racetrack veterinarian and not asking enough questions about how his horses are being treated. His i…_

✅ _Tigrado First Winner for WinStar Farm's Nashville_
  - URL: <https://www.bloodhorse.com/horse-racing/articles/291737/tigrado-first-winner-for-winstar-farms-nashville>
  - 1331 chars, 0 quotes
  - Preview: _Mana Racing's Tigrado became the first winner for WinStar Farm freshman sire Nashville in registering a 5-length victory in a 5-furlong maiden race May 7 at Horseshoe Indianapolis. Making his third st…_

✅ _From the Magazine: Debating Best Timing of Preakness_
  - URL: <https://www.bloodhorse.com/horse-racing/articles/291734/from-the-magazine-debating-best-timing-of-preakness>
  - 1189 chars, 2 quotes
  - **Sample quotes**:
    - `I love history and I believe you should respect it but, at the same time, I am also one for change,`
    - `Every sport goes through changes.`
  - Preview: _With the connections of Kentucky Derby (G1) winner Golden Tempo deciding to skip the Preakness Stakes (G1) in favor of a planned start in the Belmont Stakes (G1) June 6 at Saratoga Race Course, it mar…_

#### `anz_bloodstock`
- Items found: 6
- Tested: 3 | Success: 2/3
- Avg body length: **4674** chars | Avg quotes: **8.5**

❌ _Shinzo on speed dial for Inglis Foal Sale_
  - URL: <https://www.anzbloodstocknews.com/shinzo-on-speed-dial-for-inglis-foal-sale/>
  - Error: `Timeout`

✅ _Riverstone Lodge maintains momentum with tightly held trio_
  - URL: <https://www.anzbloodstocknews.com/riverstone-lodge-maintains-momentum-with-tightly-held-trio/>
  - 3687 chars, 9 quotes
  - **Sample quotes**:
    - `We’re always improving, but I feel like we’re pretty solid now,`
    - `We’ve capacity for about 120 horses and can still maintain attention to detail and quality.`
    - `He’s flashy. I think he’s been well noticed around the complex, for all the right reasons,`
  - Preview: _Riverstone Lodge maintains momentum with tightly held trio It was only in 2024 that Blandford-based Riverstone Lodge burst onto the scene as the leading vendor by average (three or more sold) and medi…_

✅ _Group 1-winning son of champion sire Into Mischief to make his way Down Under_
  - URL: <https://www.anzbloodstocknews.com/59588-2/>
  - 5661 chars, 8 quotes
  - **Sample quotes**:
    - `He was an outstanding racehorse, when you are rated 128 and equal best horse in the world, you are at the top of the tree,`
    - `He profiles like Street Cry. They both started their careers with half a dozen runs in Southern California before going to Dubai, they both `
    - `He’s by Into Mischief, a seven times [in succession] leading sire in America,`
  - Preview: _Group 1-winning son of champion sire Into Mischief to make his way Down Under Laurel River – a Group 1-winning son of record breaking stallion Into Mischief (Harlan’s Holiday) – will shuttle to Woodsi…_

#### `ttr_ausnz`
- Items found: 12
- Tested: 3 | Success: 3/3
- Avg body length: **9031** chars | Avg quotes: **10.3**

✅ _Titanic bidding duel results in $5.6 million for Chayan_
  - URL: <https://www.ttrausnz.com.au/edition/2026-05-08/titanic-bidding-duel-results-in-dollar56-million-for-chayan>
  - 17257 chars, 27 quotes
  - **Sample quotes**:
    - `It’s (the Inglis Chairman's Sale) a fitting end to Benedetta’s racing career for myself and the other owners involved.`
    - `Unbelievable,`
    - `I came here thinking she would make $3 million, maybe $3.6 million,`
  - Preview: _Cover image courtesy of Inglis At A Glance: Clearance for the Inglis Chairman’s Sale dropped to 73% (87%), and the aggregate was $39.085 million. 2025 ($54.4 million) and 2024 ($35.3 million). From a …_

✅ _The quartile analysis of the Inglis Australian Weanling Sale shows a tale of the_
  - URL: <https://www.ttrausnz.com.au/edition/2026-05-08/the-haves-and-have-nots-quartile-analysis-of-the-inglis-australian-weanling-sale>
  - 6027 chars, 0 quotes
  - Preview: _Cover image courtesy of Inglis Selling stock as weanlings helps breeders get some cash in their pockets ahead of the next breeding season and allows pinhookers to take a punt on a good type with some …_

✅ _At the Inglis The Chairman's Sale, TTR AusNZ uncovered a 'value buy' - an opport_
  - URL: <https://www.ttrausnz.com.au/edition/2026-05-08/value-buy-astute-bloodstock-and-cressfield-claim-ausbred-flirt-for-dollar250k>
  - 3811 chars, 4 quotes
  - **Sample quotes**:
    - `She was unlucky not to win a good race and she is a beautiful, big, scopey mare - very correct, with a great head. "One of my good clients, `
    - `We don’t mind Shinzo - he has had a really good week.`
    - `It’s great when you know a mare so well and you have that inside or in-depth knowledge to have lots of confidence when purchasing.`
  - Preview: _Lot 34 - Ausbred Flirt (Maurice {Jpn}) Buyer: Astute Bloodstock / Cressfield Vendor: Fairview Park Stud It was the combination of Louis Le Metayer’s Astute Bloodstock (FBAA) and Cressfield that put th…_

#### `smh_racing`
- Items found: 11
- Tested: 3 | Success: 3/3
- Avg body length: **5655** chars | Avg quotes: **5.3**

✅ _Race-by-race tips and previews for Gosford on Saturday_
  - URL: <https://www.smh.com.au/sport/racing/race-by-race-tips-and-previews-for-gosford-on-saturday-20260507-p5zuq8.html>
  - 9900 chars, 0 quotes
  - Preview: _Race-by-race tips and previews for Gosford on Saturday Race 1 - 11:15AM WIN $100k @ THE COAST RACEDAY 2YO HANDICAP (1200 METRES) 2. Priory Park should be at the top of his game with two runs under his…_

✅ _Pride pleased to have focused Clipperton back for familiar target_
  - URL: <https://www.smh.com.au/sport/racing/pride-pleased-to-have-focused-clipperton-back-for-familiar-target-20260507-p5zuiy.html>
  - 4369 chars, 7 quotes
  - **Sample quotes**:
    - `It’s been good using Sam again, and he’s been good for the stable,`
    - `He’s riding at a really good strike rate for us ... and he’s a different person again now. “You could see he was stale at the end, and Sam w`
    - `I want to get him into the Stradbroke, but he needs to be winning a race like this to go there,`
  - Preview: _Pride pleased to have focused Clipperton back for familiar target Three years after their winning streak with dream horse Think About It took in the Takeover Target Stakes (1200m) at Gosford, trainer …_

✅ _Family connection keeps veteran local trainer in hunt for Gosford feature_
  - URL: <https://www.smh.com.au/sport/racing/family-connection-keeps-veteran-local-trainer-in-hunt-for-gosford-feature-20260507-p5zuiu.html>
  - 2697 chars, 9 quotes
  - **Sample quotes**:
    - `They’ve burnt me out. Owners took their toll on me eventually. They said they would,`
    - `I’m retired now. When they go for a spell, I go for a spell. I’m enjoying life now.`
    - `She goes all right,`
  - Preview: _Family connection keeps veteran local trainer in hunt for Gosford feature At 78, Gosford-based group 1 winner Neil Ward says he’s had enough of training. “They’ve burnt me out. Owners took their toll …_


### 🟡 Tier B — Partial body / lede only (try-fail with fallback)

#### `singtao_racing`
- Items found: 20
- Tested: 3 | Success: 3/3
- Avg body length: **512** chars | Avg quotes: **1.0**

✅ _甜甜小記│廖康銘驚喜浪接浪_
  - URL: <https://www.stheadline.com/realtime-racing/3569977/甜甜小記廖康銘驚喜浪接浪>
  - 695 chars, 2 quotes
  - **Sample quotes**:
    - `『大番薯』 上季尾贏五班時，我已經覺得牠表現很好，當初真沒想過牠今季可更進一步，所以季內贏得四場頭馬，絕對是意料之外。廖康銘成功地把此馬的狀態保持勇銳，保養得宜，應記一功。這仗牠負頂磅， 我都有少許擔心會有點辛苦，也許上仗有過適應重磅的經驗，有助今仗發揮，牠的表現令我感到非常驚喜`
    - `我一直都低估了『大番薯』， 我沒想過牠今季可贏到四場頭馬，馬兒再次給我驚喜。`
  - Preview: _甜甜小記│廖康銘驚喜浪接浪 更新時間：19:04 2026-05-07 HKT 發佈時間：19:04 2026-05-07 HKT 發佈時間：19:04 2026-05-07 HKT 今季冠軍練馬師之爭認真激烈，剛周三季內最後一次田泥夜賽，最終暫居練馬師榜三甲的廖康銘、方嘉柏及沈集成，分別憑「大番薯」、「滿心星」與「熾烈神駒」各取一W，排名依然無變。另外，十三屆冠軍蔡約翰亦蠢蠢欲動，憑「大利好運」…_

✅ _馬場浮世繪｜岳伯仁兩新貴贏打吡橡樹前哨戰_
  - URL: <https://www.stheadline.com/realtime-racing/3569930/馬場浮世繪岳伯仁兩新貴贏打吡橡樹前哨戰>
  - 437 chars, 0 quotes
  - Preview: _馬場浮世繪｜岳伯仁兩新貴贏打吡橡樹前哨戰 更新時間：17:25 2026-05-07 HKT 發佈時間：17:25 2026-05-07 HKT 發佈時間：17:25 2026-05-07 HKT 英國車士達馬場昨(6/5)日舉行兩場被認為是打吡和橡樹大賽的前哨戰，結果兩場賽事均由岳伯仁馬房旗下馬匹勝出。 首先Amelia Earhart以兩個馬位擊敗大熱門I'm The One，贏出表列賽柴郡橡…_

✅ _沈慧林邀請周文姬張與辰入場觀戰_
  - URL: <https://www.stheadline.com/realtime-racing/3569835/沈慧林邀請周文姬張與辰入場觀戰>
  - 406 chars, 1 quotes
  - **Sample quotes**:
    - ` 飛輪閃耀`
  - Preview: _沈慧林邀請周文姬張與辰入場觀戰 更新時間：14:04 2026-05-07 HKT 發佈時間：14:04 2026-05-07 HKT 發佈時間：14:04 2026-05-07 HKT 「飛輪」系馬主沈慧林昨晚入場，為爸爸沈墨寧的「飛輪霸」打氣。昨晚沈慧林邀請了好朋友周星馳家姐周文姬和《中年好聲音》歌星張與辰一同入場，欣賞賽馬，並和「笑必勝」馬主何兆剛開心合照。 沈慧林目前是「飛輪日上」馬主之一…_


### 🔴 Tier C — Headlines only / blocked

#### `the_straight`
- Items found: 22
- Tested: 3 | Success: 0/3

❌ _‘Serious concerns’ – Tabcorp at centre of AUSTRAC investigation_
  - URL: <https://news.google.com/rss/articles/CBMikAFBVV95cUxQc1ZfbTR2bEpVN2xRc2hVTC1mN3p2UDRnYl92NFlxTzVzanhLbjRLTF9mVER6WjVyMS05WS1pOFhacDU5eks1c0FQY083NW5zYzYtMHNDMEQ2cGt5Y3dFMTdpbE8yb2szMkR3VlA4SVhxdjhWVmh5M2l5UUVlVnhqTEFWNDBiMzZjVHFQWTcxM04?oc=5>
  - Error: `trafilatura returned empty`

❌ _Computer-assisted wagering under further US scrutiny amid lawsuits, Churchill Do_
  - URL: <https://news.google.com/rss/articles/CBMivwFBVV95cUxPc2dPTmQyNzVvY3htcThnRWhZelQzbmVzUTRZc1UtVFdCbGt5c0pVVEFCMEFhQnVPaGNuejh5NDllVExoSFJzenNaaWdnZVZlTWljVFc4SzJfb1dJN1VFU3BwQk13V2wwb2ZVWC03bHdXcWMtV3E4YXB1ZUl2MzZLWl9ENTZ6VHlwSGlsS2g1RTF2WlMzQndJWEM0Sm9FLU1hOWRpSWczWm16SWxBLWszZzM3MTR3X19sU0RhZHFycw?oc=5>
  - Error: `trafilatura returned empty`

❌ _Sportsbet’s fortunes rise as Flutter makes executive change_
  - URL: <https://news.google.com/rss/articles/CBMijwFBVV95cUxNdDRCMlNWbXd5dXNMM3lMR1F2bmo1dml6cm9GOUNtUExRQXBILW10aXRFMFNuSzR5aC1hanZRVmE4MFpza1N2a1ZtR0JsQjIzbzZ6eFFlV3VXU3NzMXZ3X2tGbVpoVjR1cVd3UFFlb1NNSXdhOXdwd1BpZ2dGT0V5Q3RKTjVyS25kTjhJbW9Vcw?oc=5>
  - Error: `trafilatura returned empty`

#### `drf_news`
- Items found: 87
- Tested: 3 | Success: 0/3

❌ _Preakness 2026: Golden Tempo to skip race; Ocelli jumps in; Crude Velocity a may_
  - URL: <https://news.google.com/rss/articles/CBMinAFBVV95cUxNN2YxaXllbnJnSjJ4UHc1VTFrNGJlU0dzUXozS3pwTzlLeUVmNWVldlJScXc4aDEwbDhINEQ4MlVNQzUwUTAwWDlMYWFIZzRURlpPd1RaQi01OTdLQ0lJRko5allTZlZGVmQ4cmJ5UW9KUTVVNGZHNWNDemZHRm5KNlZOOTg0NWtTYk9oY0NYRWFTNjNBOC01Q2FuMXA?oc=5>
  - Error: `trafilatura returned empty`

❌ _Preakness 2026: Napoleon Solo's blazing works earn him final two-turn shot_
  - URL: <https://news.google.com/rss/articles/CBMingFBVV95cUxPTUpieEJxcGRmNUZ3ZHhiVFBRdENvc3pqbS1kdWM5SFZHZHFJM2xKejRKNURJa1JtOWhGWWE4M25HR25iWW8tZGUxYVVweXlRUDNyUzg2aEsyYnJ5aWRUU0RPdjRXODRGWHpmclc2ZExIMWdIRVloektUYU5qdkN2WnZTd21waFl5SkY2ZkpXVklWQ01qclByWTl2MVczdw?oc=5>
  - Error: `trafilatura returned empty`

❌ _Jourmalism, So Happy, and Stronghold share the racetrack and some history_
  - URL: <https://news.google.com/rss/articles/CBMilwFBVV95cUxOOGFGUWQyTUY2VjlaU0ZadVA5aldjYXVSdm9hSzFPanR1NUdBNWhJVDViZ1ZDei1vZHFtQWJFbWZLM0FJWEN4bWFUZk0yZzA4dno5S3F5eENhSW5IemdkbGxQUXZ2NXp2cWZkd1lZV29kR1ZLRnRiZWlTaHp2LXU4Mi1qZURPc05LZDQ4ZmpieDZla2dVN0c4?oc=5>
  - Error: `trafilatura returned empty`

#### `equidia_racing`
- Items found: 20
- Tested: 3 | Success: 1/3
- Avg body length: **1364** chars | Avg quotes: **0.0**

❌ _Quinté+ du vendredi 8 mai à Lyon-Parilly : Thor Lightning en route vers un premi_
  - URL: <https://www.equidia.fr/articles/quinte/quinte-du-vendredi-8-mai-a-lyon-parilly-thor-lightning-en-route-vers-un-premier-evenement>
  - Error: `HTTP 504`

✅ _Les notes des partants du Quinté+ de ce vendredi 8 mai_
  - URL: <https://www.equidia.fr/articles/pour-preparer-vos-paris/les-notes-des-partants-du-quinte-de-ce-vendredi-8-mai>
  - 1364 chars, 0 quotes
  - Preview: _Les notes des partants du Quinté+ de ce vendredi 8 mai Avec cet outil, Equidia vous propose un classement théorique basé sur des données spécifiques comme les conditions de course, les aptitudes, la f…_

❌ _Quinté Express : Analyse du Quinté+ du vendredi 8 mai_
  - URL: <https://www.equidia.fr/articles/pour-preparer-vos-paris/quinte-express-analyse-du-quinte-du-vendredi-8-mai>
  - Error: `HTTP 504`


### ⚠️ NO DATA — Scraper returned empty list

#### `punters_au`
- Items found: 0
- Tested: 0 | Success: 0/0

#### `racing_com`
- Items found: 0
- Tested: 0 | Success: 0/0

#### `tospo_keiba`
- Items found: 0
- Tested: 0 | Success: 0/0

#### `netkeiba_news`
- Items found: 0
- Tested: 0 | Success: 0/0

#### `racenet_news`
- Items found: 0
- Tested: 0 | Success: 0/0

#### `daily_telegraph`
- Items found: 0
- Tested: 0 | Success: 0/0


---

## Recommendations

- **Tier A (6 sources)**: Stage 3 pipeline 直接用 trafilatura。
- **Tier B (1 sources)**: Try-fail 模式；抓到 lede 用 lede，否則回退到標題。
- **Tier C (3 sources)**: 只有標題可用。對高權威來源（如 Racing Post），保留標題中的引號 fragment 作為 partial quote。