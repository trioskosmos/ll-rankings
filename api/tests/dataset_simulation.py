import httpx
import json

BASE_URL = "http://localhost:8000/api/v1"
FRANCHISE = "liella"
SUBGROUP = "All Songs"

# The raw data provided in the request
RAW_DATA = """
Rumi	kusa	Neptune	HooKnows	Honobruh	Dyrea	Wumbo
1. ニュートラル - KALEIDOSCORE	1. What a Wonderful Dream!! - Liella!	1. Dazzling Game - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	1. Day1 - Liella!	1. ルカ - ウィーン・マルガレーテ	1. Shooting Voice!! - Liella!	1. QUESTION99 - Liella!
2. 不可視なブルー - KALEIDOSCORE	2. Wish Song - Liella!	2. ガラスボールリジェクション - 若菜四季	2. この街でいまキミと - Liella!	2. ノンフィクション!! - Liella!	2. 始まりは君の空 - Liella!	2. ニュートラル - KALEIDOSCORE
3. ベロア - KALEIDOSCORE	3. 未来予報ハレルヤ！ - Liella!	3. 茜心 - 米女メイ	3. Dazzling Game - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	3. Aspire - Liella!	3. START!! True dreams - Liella!	3. ルカ - ウィーン・マルガレーテ
4. 真っ赤。 - Liella!	4. Starlight Prologue - Liella!	4. 罪DA・YO・NE - 米女メイ、若菜四季	4. ルカ - ウィーン・マルガレーテ	4. いつものピースサイン - Liella!	4. Dream Rainbow - Liella!	4. Day1 - Liella!
5. Bubble Rise - 澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	5. 探して！Future - Liella!	5. UNIVERSE!! - Liella!	5. Bubble Rise - 澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	5. Dazzling Game - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	5. 私のSymphony - Liella!	5. ワイルドカード - 鬼塚冬毬
6. 絶対的LOVER - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	6. 始まりは君の空 - Liella!	6. 想われマリオネット - 澁谷かのん、嵐 千砂都、葉月 恋、鬼塚夏美、ウィーン・マルガレーテ	6. ビタミンSUMMER！ - Liella!	6. 始まりは君の空 - Liella!	6. UNIVERSE!! - Liella!	6. 勇気のカケラ - 嵐 千砂都
7. Welcome to 僕らのセカイ - Liella!	7. 笑顔のPromise - Liella!	7. Second Sparkle - Liella!	7. ワイルドカード - 鬼塚冬毬	7. 真っ赤。 - Liella!	7. 揺らぐわ - Liella!	7. LiLiA - 若菜四季
8. MIRACLE NEW STORY - Liella!	8. WE WILL!! - Liella!	8. OPEN THE G☆TE!!! - Liella!	8. オレンジのままで - Liella!	8. Rhythm - 嵐 千砂都	8. Aspire - Liella!	8. Sky Linker - 米女メイ
9. 想われマリオネット - 澁谷かのん、嵐 千砂都、葉月 恋、鬼塚夏美、ウィーン・マルガレーテ	9. Aspire - Liella!	9. 結ぶメロディ - Liella!	9. Starlight Prologue - Liella!	9. Tiny Stars - 澁谷かのん、唐 可可	9. ユニゾン - Liella!	9. Wish Song - Liella!
10. OPEN THE G☆TE!!! - Liella!	10. エーデルシュタイン - ウィーン・マルガレーテ	10. DAISUKI FULL POWER - Liella!	10. カメリアの囁き - KALEIDOSCORE	10. Ringing! - 嵐 千砂都	10. だから僕らは鳴らすんだ！ - Liella!	10. Till Sunrise - Sunny Passion
11. QUESTION99 - Liella!	11. ティーンエイジ・ロンリネス - 唐 可可、平安名すみれ、桜小路きな子、鬼塚冬毬	11. 未来は風のように - Liella!	11. ディストーション - CatChu!	11. Just woo!! - 平安名すみれ	11. TO BE CONTINUED - Liella!	11. カメリアの囁き - KALEIDOSCORE
12. Special Color - Liella!	12. 常夏☆サンシャイン - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ	12. Starlight Prologue - Liella!	12. 未来は風のように - Liella!	12. Starlight Prologue - Liella!	12. FANTASTiC - Liella!	12. 不可視なブルー - KALEIDOSCORE
13. High！モチベーション - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美、ウィーン・マルガレーテ、鬼塚冬毬	13. High！モチベーション - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美、ウィーン・マルガレーテ、鬼塚冬毬	13. オレンジのままで - Liella!	13. Special Color - Liella!	13. 結ぶメロディ - Liella!	13. GOING UP - Liella!	13. Aspire - Liella!
14. Starlight Prologue - Liella!	14. Shooting Voice!! - Liella!	14. ニュートラル - KALEIDOSCORE	14. ニュートラル - KALEIDOSCORE	14. 未来は風のように - Liella!	14. 未来は風のように - Liella!	14. 真っ赤。 - Liella!
15. ティーンエイジ・ロンリネス - 唐 可可、平安名すみれ、桜小路きな子、鬼塚冬毬	15. Chance Day, Chance Way！ - Liella!	15. ワイルドカード - 鬼塚冬毬	15. Let's be ONE - Liella!	15. 青空を待ってる - 澁谷かのん	15. Dazzling Game - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	15. Just woo!! - 平安名すみれ
16. 全力ライオット - CatChu!	16. 追いかける夢の先で - Liella!	16. Jellyfish - 5yncri5e!	16. LiLiA - 若菜四季	16. 水色のSunday - 唐 可可	16. ビタミンSUMMER！ - Liella!	16. ベロア - KALEIDOSCORE
17. 罪DA・YO・NE - 米女メイ、若菜四季	17. Jellyfish - 5yncri5e!	17. Sky Linker - 米女メイ	17. ノンフィクション!! - Liella!	17. 星屑クルージング - 唐 可可	17. Second Sparkle - Liella!	17. ノンフィクション!! - Liella!
18. ファンダメンタル - 唐 可可	18. Dream Rainbow - Liella!	18. Aspire - Liella!	18. QUESTION99 - Liella!	18. ビタミンSUMMER！ - Liella!	18. Wish Song - Liella!	18. Dazzling Game - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬
19. 影遊び - CatChu!	19. だから僕らは鳴らすんだ！ - Liella!	19. パステルコラージュ - 鬼塚夏美	19. だから僕らは鳴らすんだ！ - Liella!	19. Oh！レディ・ステディ・ポジティブ - 唐 可可	19. Chance Day, Chance Way！ - Liella!	19. 始まりは君の空 - Liella!
20. 君・街・空・星 - Liella!	20. Dancing Heart La-Pa-Pa-Pa! - Liella!	20. 真っ赤。 - Liella!	20. Tiny Stars - 澁谷かのん、唐 可可	20. LiLiA - 若菜四季	20. キラーキューン☆ - Liella!	20. 私のSymphony - Liella!
21. 茜心 - 米女メイ	21. ファンダメンタル - 唐 可可	21. Let's be ONE - Liella!	21. 揺らぐわ - Liella!	21. Dancing Raspberry - 5yncri5e!	21. 真っ赤。 - Liella!	21. Special Color - Liella!
22. キラーキューン☆ - Liella!	22. OPEN THE G☆TE!!! - Liella!	22. LiLiA - 若菜四季	22. What a Wonderful Dream!! - Liella!	22. QUESTION99 - Liella!	22. Jellyfish - 5yncri5e!	22. 探して！Future - Liella!
23. LiLiA - 若菜四季	23. 迷宮讃歌 - 葉月 恋	23. 絶対的LOVER - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	23. いつものピースサイン - Liella!	23. ニュートラル - KALEIDOSCORE	23. Starlight Prologue - Liella!	23. 結び葉 - 葉月 恋
24. HAPPY TO DO WA！ - 唐 可可、平安名すみれ、葉月 恋	24. ビタミンSUMMER！ - Liella!	24. いつものピースサイン - Liella!	24. アイコトバ！ - Liella!	24. ファンダメンタル - 唐 可可	24. スーパースター!! - Liella!	24. 絶対的LOVER - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬
25. 未来は風のように - Liella!	25. 瞬きの先へ - Liella!	25. アイコトバ！ - Liella!	25. 始まりは君の空 - Liella!	25. 常夏☆サンシャイン - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ	25. アイコトバ！ - Liella!	25. スーパースター!! - Liella!
26. POP TALKING - Liella!	26. Dazzling Game - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	26. キラーキューン☆ - Liella!	26. START!! True dreams - Liella!	26. Summer Escape!! - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	26. 未来予報ハレルヤ！ - Liella!	26. 色づいて透明 - Liella!
27. Second Sparkle - Liella!	27. Thank you Good morning - 5yncri5e!	27. 瞬きの先へ - Liella!	27. Butterfly Wing - ウィーン・マルガレーテ	27. 茜心 - 米女メイ	27. Sing！Shine！Smile！ - Liella!	27. いつものピースサイン - Liella!
28. みてろ！ - 平安名すみれ	28. 私のSymphony - Liella!	28. 君・街・空・星 - Liella!	28. ほんのちょっぴり - 澁谷かのん	28. 結び葉 - 葉月 恋	28. この街でいまキミと - Liella!	28. Starlight Prologue - Liella!
29. クレッシェンドゆ・ら - 唐 可可、葉月 恋	29. A Little Love - 5yncri5e!	29. Special Color - Liella!	29. Second Sparkle - Liella!	29. Jellyfish - 5yncri5e!	29. Dancing Raspberry - 5yncri5e!	29. Tiny Stars - 澁谷かのん、唐 可可
30. スーパースター!! - Liella!	30. 未来は風のように - Liella!	30. 名前呼びあうように - Liella!	30. Jellyfish - 5yncri5e!	30. ガラスボールリジェクション - 若菜四季	30. オルタネイト - CatChu!	30. Stella! - 澁谷かのん、嵐 千砂都、平安名すみれ
31. Chance Day, Chance Way！ - Liella!	31. Butterfly Wing - ウィーン・マルガレーテ	31. 水しぶきのサイン - Liella!	31. 真っ赤。 - Liella!	31. Eyeをちょうだい - 鬼塚夏美	31. いつものピースサイン - Liella!	31. だから僕らは鳴らすんだ！ - Liella!
32. オルタネイト - CatChu!	32. 未来の音が聴こえる - Liella!	32. オルタネイト - CatChu!	32. オルタネイト - CatChu!	32. 青春HOPPERS - Liella!	32. LiLiA - 若菜四季	32. オルタネイト - CatChu!
33. 始まりは君の空 - Liella!	33. START!! True dreams - Liella!	33. ビタミンSUMMER！ - Liella!	33. 不可視なブルー - KALEIDOSCORE	33. Day1 - Liella!	33. 不可視なブルー - KALEIDOSCORE	33. MIRACLE NEW STORY - Liella!
34. 未来予報ハレルヤ！ - Liella!	34. DAISUKI FULL POWER - Liella!	34. ファンダメンタル - 唐 可可	34. Aspire - Liella!	34. シェキラ☆☆☆ - Liella!	34. Go!! リスタート - Liella!	34. ガラスボールリジェクション - 若菜四季
35. 常夏☆サンシャイン - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ	35. カメリアの囁き - KALEIDOSCORE	35. 未来の音が聴こえる - Liella!	35. シェキラ☆☆☆ - Liella!	35. ワイルドカード - 鬼塚冬毬	35. Special Color - Liella!	35. Go!! リスタート - Liella!
36. Just woo!! - 平安名すみれ	36. オレンジのままで - Liella!	36. Including you - Liella!	36. 笑顔のPromise - Liella!	36. OPEN THE G☆TE!!! - Liella!	36. カメリアの囁き - KALEIDOSCORE	36. ディストーション - CatChu!
37. Aspire - Liella!	37. 青空を待ってる - 澁谷かのん	37. Starry Prayer - 平安名すみれ	37. Till Sunrise - Sunny Passion	37. トゥ トゥ トゥ！ - Liella!	37. Jump Into the New World - Liella!	37. Second Sparkle - Liella!
38. Jump Into the New World - Liella!	38. ユニゾン - Liella!	38. ひとひらだけ - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	38. Eyeをちょうだい - 鬼塚夏美	38. パステルコラージュ - 鬼塚夏美	38. ノンフィクション!! - Liella!	38. 揺らぐわ - Liella!
39. シェキラ☆☆☆ - Liella!	39. 罪DA・YO・NE - 米女メイ、若菜四季	39. Bubble Rise - 澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	39. 勇気のカケラ - 嵐 千砂都	39. Let's be ONE - Liella!	39. ニュートラル - KALEIDOSCORE	39. Bubble Rise - 澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬
40. Stella! - 澁谷かのん、嵐 千砂都、平安名すみれ	40. 星屑クルージング - 唐 可可	40. エーデルシュタイン - ウィーン・マルガレーテ	40. 私のSymphony - Liella!	40. キラーキューン☆ - Liella!	40. 結び葉 - 葉月 恋	40. TO BE CONTINUED - Liella!
41. Thank you Good morning - 5yncri5e!	41. ミッドナイトラプソディ - 葉月 恋	41. リバーブ - 葉月 恋	41. FANTASTiC - Liella!	41. ほんのちょっぴり - 澁谷かのん	41. WE WILL!! - Liella!	41. What a Wonderful Dream!! - Liella!
42. ガラスボールリジェクション - 若菜四季	42. リバーブ - 葉月 恋	42. Tiny Stars - 澁谷かのん、唐 可可	42. 1.2.3！ - Liella!	42. Bubble Rise - 澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	42. 星屑クルージング - 唐 可可	42. ユートピアマジック - Liella!
43. 笑顔のPromise - Liella!	43. Welcome to 僕らのセカイ - Liella!	43. ノンフィクション!! - Liella!	43. 茜心 - 米女メイ	43. スーパースター!! - Liella!	43. 1.2.3！ - Liella!	43. 全力ライオット - CatChu!
44. カメリアの囁き - KALEIDOSCORE	44. Eyeをちょうだい - 鬼塚夏美	44. Eyeをちょうだい - 鬼塚夏美	44. ベロア - KALEIDOSCORE	44. 私のSymphony - Liella!	44. Eyeをちょうだい - 鬼塚夏美	44. 常夏☆サンシャイン - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ
45. What a Wonderful Dream!! - Liella!	45. Over Over - 澁谷かのん	45. シェキラ☆☆☆ - Liella!	45. ファイティングコール - Liella!	45. Time to go - Liella!	45. 名前呼びあうように - Liella!	45. ファイティングコール - Liella!
46. Wish Song - Liella!	46. 真っ赤。 - Liella!	46. Butterfly Wing - ウィーン・マルガレーテ	46. ユニゾン - Liella!	46. ディストーション - CatChu!	46. 未来の音が聴こえる - Liella!	46. バイバイしちゃえば！？ - Liella!
47. Dancing Raspberry - 5yncri5e!	47. ほんのちょっぴり - 澁谷かのん	47. 全力ライオット - CatChu!	47. WE WILL!! - Liella!	47. FANTASTiC - Liella!	47. 心キラララ - 澁谷かのん	47. HAPPY TO DO WA！ - 唐 可可、平安名すみれ、葉月 恋
48. ビタミンSUMMER！ - Liella!	48. 全力ライオット - CatChu!	48. START!! True dreams - Liella!	48. 想われマリオネット - 澁谷かのん、嵐 千砂都、葉月 恋、鬼塚夏美、ウィーン・マルガレーテ	48. Butterfly Wing - ウィーン・マルガレーテ	48. オレンジのままで - Liella!	48. クレッシェンドゆ・ら - 唐 可可、葉月 恋
49. Jellyfish - 5yncri5e!	49. Primary - Liella!	49. ほんのちょっぴり - 澁谷かのん	49. Jump Into the New World - Liella!	49. What a Wonderful Dream!! - Liella!	49. DAISUKI FULL POWER - Liella!	49. ビタミンSUMMER！ - Liella!
50. 1.2.3！ - Liella!	50. ガラスボールリジェクション - 若菜四季	50. 不可視なブルー - KALEIDOSCORE	50. スター宣言 - Liella!	50. POP TALKING - Liella!	50. Tiny Stars - 澁谷かのん、唐 可可	50. キラーキューン☆ - Liella!
51. 結ぶメロディ - Liella!	51. Flyer’s High - 嵐 千砂都	51. あふれる言葉 - 桜小路きな子	51. Sky Linker - 米女メイ	51. だいすきのうた - 澁谷かのん	51. QUESTION99 - Liella!	51. Thank you Good morning - 5yncri5e!
52. ヒロインズ☆ランウェイ - 平安名すみれ	52. 結び葉 - 葉月 恋	52. Oh！レディ・ステディ・ポジティブ - 唐 可可	52. Just woo!! - 平安名すみれ	52. ベロア - KALEIDOSCORE	52. 君・街・空・星 - Liella!	52. スター宣言 - Liella!
53. 微熱のワルツ - 葉月 恋	53. 名前呼びあうように - Liella!	53. スーパースター!! - Liella!	53. 罪DA・YO・NE - 米女メイ、若菜四季	53. DAISUKI FULL POWER - Liella!	53. Day1 - Liella!	53. HOT PASSION!! - Sunny Passion
54. ノンフィクション!! - Liella!	54. スーパースター!! - Liella!	54. 笑顔のPromise - Liella!	54. Dancing Raspberry - 5yncri5e!	54. Chance Day, Chance Way！ - Liella!	54. 水しぶきのサイン - Liella!	54. START!! True dreams - Liella!
55. Let's be ONE - Liella!	55. アイコトバ！ - Liella!	55. 11th moon - ウィーン・マルガレーテ、鬼塚冬毬	55. キラーキューン☆ - Liella!	55. START!! True dreams - Liella!	55. 茜心 - 米女メイ	55. Welcome to 僕らのセカイ - Liella!
56. Tiny Stars - 澁谷かのん、唐 可可	56. バイバイしちゃえば！？ - Liella!	56. Over Over - 澁谷かのん	56. 結び葉 - 葉月 恋	56. グソクムシのうた - 平安名すみれ	56. POP TALKING - Liella!	56. Jump Into the New World - Liella!
57. Sky Linker - 米女メイ	57. Oh！レディ・ステディ・ポジティブ - 唐 可可	57. MIRACLE NEW STORY - Liella!	57. A Little Love - 5yncri5e!	57. Dreaming Energy - Liella!	57. 青春HOPPERS - Liella!	57. Including you - Liella!
58. ルカ - ウィーン・マルガレーテ	58. Bubble Rise - 澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	58. パレードはいつも - 米女メイ	58. エーデルシュタイン - ウィーン・マルガレーテ	58. ミッドナイトラプソディ - 葉月 恋	58. Oh！レディ・ステディ・ポジティブ - 唐 可可	58. Flyer’s High - 嵐 千砂都
59. プライム・アドベンチャー - Liella!	59. 心キラララ - 澁谷かのん	59. Sing！Shine！Smile！ - Liella!	59. UNIVERSE!! - Liella!	59. dolce - ウィーン・マルガレーテ	59. 影遊び - CatChu!	59. Within a Dream - Liella!
60. Starry Prayer - 平安名すみれ	60. てくてく日和 - 桜小路きな子	60. 追いかける夢の先で - Liella!	60. Wish Song - Liella!	60. 絶対的LOVER - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	60. 水色のSunday - 唐 可可	60. POP TALKING - Liella!
61. FANTASTiC - Liella!	61. 絶対的LOVER - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	61. dolce - ウィーン・マルガレーテ	61. 水しぶきのサイン - Liella!	61. Thank you Good morning - 5yncri5e!	61. High！モチベーション - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美、ウィーン・マルガレーテ、鬼塚冬毬	61. 未来予報ハレルヤ！ - Liella!
62. Dancing Heart La-Pa-Pa-Pa! - Liella!	62. みてろ！ - 平安名すみれ	62. ファイティングコール - Liella!	62. Including you - Liella!	62. 揺らぐわ - Liella!	62. ミッドナイトラプソディ - 葉月 恋	62. 変わらないすべて - 澁谷かのん、嵐 千砂都
63. Summer Escape!! - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	63. Hoshizora Monologue - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	63. 揺らぐわ - Liella!	63. Departure - Liella!	63. ひとひらだけ - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	63. 笑顔のPromise - Liella!	63. みてろ！ - 平安名すみれ
64. ユートピアマジック - Liella!	64. スター宣言 - Liella!	64. スター宣言 - Liella!	64. クレッシェンドゆ・ら - 唐 可可、葉月 恋	64. Primary - Liella!	64. ガラスボールリジェクション - 若菜四季	64. 笑顔のPromise - Liella!
65. エンドレスサーキット - 唐 可可	65. ワイルドカード - 鬼塚冬毬	65. Hoshizora Monologue - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	65. 全力ライオット - CatChu!	65. 微熱のワルツ - 葉月 恋	65. Dancing Heart La-Pa-Pa-Pa! - Liella!	65. Free Flight - 澁谷かのん
66. WE WILL!! - Liella!	66. Jump Into the New World - Liella!	66. 常夏☆サンシャイン - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ	66. MIRACLE NEW STORY - Liella!	66. Second Sparkle - Liella!	66. ディストーション - CatChu!	66. 罪DA・YO・NE - 米女メイ、若菜四季
67. Dazzling Game - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	67. TO BE CONTINUED - Liella!	67. 始まりは君の空 - Liella!	67. 影遊び - CatChu!	67. Special Color - Liella!	67. A Little Love - 5yncri5e!	67. Jellyfish - 5yncri5e!
68. Go!! リスタート - Liella!	68. Dancing Raspberry - 5yncri5e!	68. TO BE CONTINUED - Liella!	68. Thank you Good morning - 5yncri5e!	68. ティーンエイジ・ロンリネス - 唐 可可、平安名すみれ、桜小路きな子、鬼塚冬毬	68. 追いかける夢の先で - Liella!	68. WE WILL!! - Liella!
69. Dreamer Coaster - 澁谷かのん	69. UNIVERSE!! - Liella!	69. プライム・アドベンチャー - Liella!	69. パステルコラージュ - 鬼塚夏美	69. 不可視なブルー - KALEIDOSCORE	69. シェキラ☆☆☆ - Liella!	69. 追いかける夢の先で - Liella!
70. バイバイしちゃえば！？ - Liella!	70. LiLiA - 若菜四季	70. 青春HOPPERS - Liella!	70. 青春HOPPERS - Liella!	70. 君を想う花になる - 嵐 千砂都	70. 色づいて透明 - Liella!	70. OPEN THE G☆TE!!! - Liella!
71. ディストーション - CatChu!	71. GOING UP - Liella!	71. A Little Love - 5yncri5e!	71. 瞬きの先へ - Liella!	71. Over Over - 澁谷かのん	71. バイバイしちゃえば！？ - Liella!	71. Butterfly Wing - ウィーン・マルガレーテ
72. Dears - 葉月 恋	72. Dreaming Energy - Liella!	72. 結び葉 - 葉月 恋	72. 未来予報ハレルヤ！ - Liella!	72. 未来予報ハレルヤ！ - Liella!	72. Bubble Rise - 澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	72. エーデルシュタイン - ウィーン・マルガレーテ
73. Blooming Dance！Dance！ - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	73. ファイティングコール - Liella!	73. ディストーション - CatChu!	73. Shooting Voice!! - Liella!	73. Dream Rainbow - Liella!	73. Within a Dream - Liella!	73. 茜心 - 米女メイ
74. Shooting Voice!! - Liella!	74. エンドレスサーキット - 唐 可可	74. ティーンエイジ・ロンリネス - 唐 可可、平安名すみれ、桜小路きな子、鬼塚冬毬	74. 常夏☆サンシャイン - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ	74. Departure - Liella!	74. MIRACLE NEW STORY - Liella!	74. DAISUKI FULL POWER - Liella!
75. いつものピースサイン - Liella!	75. Stella! - 澁谷かのん、嵐 千砂都、平安名すみれ	75. クレッシェンドゆ・ら - 唐 可可、葉月 恋	75. Oh！レディ・ステディ・ポジティブ - 唐 可可	75. Flyer’s High - 嵐 千砂都	75. エーデルシュタイン - ウィーン・マルガレーテ	75. Dream Rainbow - Liella!
76. 11th moon - ウィーン・マルガレーテ、鬼塚冬毬	76. 勇気のカケラ - 嵐 千砂都	76. HAPPY TO DO WA！ - 唐 可可、平安名すみれ、葉月 恋	76. GOING UP - Liella!	76. 心キラララ - 澁谷かのん	76. 全力ライオット - CatChu!	76. ミッドナイトラプソディ - 葉月 恋
77. Anniversary - 唐 可可	77. 想われマリオネット - 澁谷かのん、嵐 千砂都、葉月 恋、鬼塚夏美、ウィーン・マルガレーテ	77. POP TALKING - Liella!	77. Primary - Liella!	77. WE WILL!! - Liella!	77. 結ぶメロディ - Liella!	77. Sing！Shine！Smile！ - Liella!
78. A Little Love - 5yncri5e!	78. いつものピースサイン - Liella!	78. Welcome to 僕らのセカイ - Liella!	78. Flyer’s High - 嵐 千砂都	78. Dears - 葉月 恋	78. Thank you Good morning - 5yncri5e!	78. 未来は風のように - Liella!
79. 迷宮讃歌 - 葉月 恋	79. Go!! リスタート - Liella!	79. てくてく日和 - 桜小路きな子	79. 星屑クルージング - 唐 可可	79. 1.2.3！ - Liella!	79. ファイティングコール - Liella!	79. High！モチベーション - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美、ウィーン・マルガレーテ、鬼塚冬毬
80. Oh！レディ・ステディ・ポジティブ - 唐 可可	80. 揺らぐわ - Liella!	80. Primary - Liella!	80. 11th moon - ウィーン・マルガレーテ、鬼塚冬毬	80. 全力ライオット - CatChu!	80. 青空を待ってる - 澁谷かのん	80. Over Over - 澁谷かのん
81. DAISUKI FULL POWER - Liella!	81. キラーキューン☆ - Liella!	81. ルカ - ウィーン・マルガレーテ	81. 青空を待ってる - 澁谷かのん	81. アイコトバ！ - Liella!	81. Welcome to 僕らのセカイ - Liella!	81. 1.2.3！ - Liella!
82. dolce - ウィーン・マルガレーテ	82. クレッシェンドゆ・ら - 唐 可可、葉月 恋	82. Anniversary - 唐 可可	82. Dears - 葉月 恋	82. 11th moon - ウィーン・マルガレーテ、鬼塚冬毬	82. ひとひらだけ - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	82. 君・街・空・星 - Liella!
83. 探して！Future - Liella!	83. Starry Prayer - 平安名すみれ	83. Message - 平安名すみれ	83. 追いかける夢の先で - Liella!	83. 勇気のカケラ - 嵐 千砂都	83. 勇気のカケラ - 嵐 千砂都	83. オレンジのままで - Liella!
84. Dreaming Energy - Liella!	84. ヒロインズ☆ランウェイ - 平安名すみれ	84. 私のSymphony - Liella!	84. 君・街・空・星 - Liella!	84. ユニゾン - Liella!	84. クレッシェンドゆ・ら - 唐 可可、葉月 恋	84. Dreaming Energy - Liella!
85. 追いかける夢の先で - Liella!	85. パステルコラージュ - 鬼塚夏美	85. Rhythm - 嵐 千砂都	85. Over Over - 澁谷かのん	85. A Little Love - 5yncri5e!	85. トゥ トゥ トゥ！ - Liella!	85. Chance Day, Chance Way！ - Liella!
86. Day1 - Liella!	86. 茜心 - 米女メイ	86. Dancing Raspberry - 5yncri5e!	86. Within a Dream - Liella!	86. 追いかける夢の先で - Liella!	86. ワイルドカード - 鬼塚冬毬	86. Starry Prayer - 平安名すみれ
87. 揺らぐわ - Liella!	87. 結ぶメロディ - Liella!	87. ベロア - KALEIDOSCORE	87. スーパースター!! - Liella!	87. だから僕らは鳴らすんだ！ - Liella!	87. Over Over - 澁谷かのん	87. アイコトバ！ - Liella!
88. 青春HOPPERS - Liella!	88. 駆けるメリーゴーランド - 嵐 千砂都	88. Chance Day, Chance Way！ - Liella!	88. Chance Day, Chance Way！ - Liella!	88. 瞬きの先へ - Liella!	88. Free Flight - 澁谷かのん	88. ティーンエイジ・ロンリネス - 唐 可可、平安名すみれ、桜小路きな子、鬼塚冬毬
89. 私のSymphony - Liella!	89. 君を想う花になる - 嵐 千砂都	89. Thank you Good morning - 5yncri5e!	89. High！モチベーション - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美、ウィーン・マルガレーテ、鬼塚冬毬	89. 迷宮讃歌 - 葉月 恋	89. OPEN THE G☆TE!!! - Liella!	89. Rhythm - 嵐 千砂都
90. Ringing! - 嵐 千砂都	90. グソクムシのうた - 平安名すみれ	90. ミッドナイトラプソディ - 葉月 恋	90. ヒロインズ☆ランウェイ - 平安名すみれ	90. 探して！Future - Liella!	90. Just woo!! - 平安名すみれ	90. A Little Love - 5yncri5e!
91. アイコトバ！ - Liella!	91. 色づいて透明 - Liella!	91. Jump Into the New World - Liella!	91. てくてく日和 - 桜小路きな子	91. この街でいまキミと - Liella!	91. 絶対的LOVER - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	91. ビギナーズRock!! - 桜小路きな子
92. Dream Rainbow - Liella!	92. パレードはいつも - 米女メイ	92. QUESTION99 - Liella!	92. ファンダメンタル - 唐 可可	92. エーデルシュタイン - ウィーン・マルガレーテ	92. ファンダメンタル - 唐 可可	92. 未来の音が聴こえる - Liella!
93. Eyeをちょうだい - 鬼塚夏美	93. Rhythm - 嵐 千砂都	93. ヒロインズ☆ランウェイ - 平安名すみれ	93. ガラスボールリジェクション - 若菜四季	93. MIRACLE NEW STORY - Liella!	93. 常夏☆サンシャイン - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ	93. パステルコラージュ - 鬼塚夏美
94. START!! True dreams - Liella!	94. シェキラ☆☆☆ - Liella!	94. Wish Song - Liella!	94. Free Flight - 澁谷かのん	94. Anniversary - 唐 可可	94. スター宣言 - Liella!	94. ユニゾン - Liella!
95. Message - 平安名すみれ	95. Message - 平安名すみれ	95. 水色のSunday - 唐 可可	95. 絶対的LOVER - Liella!、澁谷かのん、ウィーン・マルガレーテ、鬼塚冬毬	95. Memories - 澁谷かのん	95. ティーンエイジ・ロンリネス - 唐 可可、平安名すみれ、桜小路きな子、鬼塚冬毬	95. 青春HOPPERS - Liella!
96. TO BE CONTINUED - Liella!	96. Sing！Shine！Smile！ - Liella!	96. カメリアの囁き - KALEIDOSCORE	96. Memories - 澁谷かのん	96. バイバイしちゃえば！？ - Liella!	96. Starry Prayer - 平安名すみれ	96. 心キラララ - 澁谷かのん
97. だから僕らは鳴らすんだ！ - Liella!	97. Tiny Stars - 澁谷かのん、唐 可可	97. Dreaming Energy - Liella!	97. Rhythm - 嵐 千砂都	97. カメリアの囁き - KALEIDOSCORE	97. What a Wonderful Dream!! - Liella!	97. 水しぶきのサイン - Liella!
98. Memories - 澁谷かのん	98. Second Sparkle - Liella!	98. Within a Dream - Liella!	98. OPEN THE G☆TE!!! - Liella!	98. 影遊び - CatChu!	98. 11th moon - ウィーン・マルガレーテ、鬼塚冬毬	98. FANTASTiC - Liella!
99. 星屑クルージング - 唐 可可	99. 1.2.3！ - Liella!	99. Day1 - Liella!	99. Stella! - 澁谷かのん、嵐 千砂都、平安名すみれ	99. 想われマリオネット - 澁谷かのん、嵐 千砂都、葉月 恋、鬼塚夏美、ウィーン・マルガレーテ	99. 罪DA・YO・NE - 米女メイ、若菜四季	99. Dancing Heart La-Pa-Pa-Pa! - Liella!
100. 色づいて透明 - Liella!	100. 不可視なブルー - KALEIDOSCORE	100. ビギナーズRock!! - 桜小路きな子	100. 君を想う花になる - 嵐 千砂都	100. Blooming Dance！Dance！ - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	100. 君を想う花になる - 嵐 千砂都	100. 影遊び - CatChu!
101. スター宣言 - Liella!	101. ニュートラル - KALEIDOSCORE	101. WE WILL!! - Liella!	101. Blooming Dance！Dance！ - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	101. Starry Prayer - 平安名すみれ	101. Blooming Dance！Dance！ - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	101. UNIVERSE!! - Liella!
102. UNIVERSE!! - Liella!	102. ビギナーズRock!! - 桜小路きな子	102. 影遊び - CatChu!	102. 結ぶメロディ - Liella!	102. HAPPY TO DO WA！ - 唐 可可、平安名すみれ、葉月 恋	102. だいすきのうた - 澁谷かのん	102. Oh！レディ・ステディ・ポジティブ - 唐 可可
103. Over Over - 澁谷かのん	103. オルタネイト - CatChu!	103. 星屑クルージング - 唐 可可	103. 微熱のワルツ - 葉月 恋	103. リバーブ - 葉月 恋	103. 迷宮讃歌 - 葉月 恋	103. 星屑クルージング - 唐 可可
104. 勇気のカケラ - 嵐 千砂都	104. Summer Escape!! - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	104. High！モチベーション - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美、ウィーン・マルガレーテ、鬼塚冬毬	104. Sing！Shine！Smile！ - Liella!	104. オルタネイト - CatChu!	104. Hoshizora Monologue - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	104. Eyeをちょうだい - 鬼塚夏美
105. Free Flight - 澁谷かのん	105. 君・街・空・星 - Liella!	105. What a Wonderful Dream!! - Liella!	105. 未来の音が聴こえる - Liella!	105. Within a Dream - Liella!	105. パステルコラージュ - 鬼塚夏美	105. Hoshizora Monologue - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋
106. HOT PASSION!! - Sunny Passion	106. ユートピアマジック - Liella!	106. Memories - 澁谷かのん	106. Hoshizora Monologue - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	106. ヒロインズ☆ランウェイ - 平安名すみれ	106. プライム・アドベンチャー - Liella!	106. 想われマリオネット - 澁谷かのん、嵐 千砂都、葉月 恋、鬼塚夏美、ウィーン・マルガレーテ
107. エーデルシュタイン - ウィーン・マルガレーテ	107. Special Color - Liella!	107. Just woo!! - 平安名すみれ	107. ビギナーズRock!! - 桜小路きな子	107. クレッシェンドゆ・ら - 唐 可可、葉月 恋	107. Summer Escape!! - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	107. この街でいまキミと - Liella!
108. 青空を待ってる - 澁谷かのん	108. Dears - 葉月 恋	108. 探して！Future - Liella!	108. Anniversary - 唐 可可	108. みてろ！ - 平安名すみれ	108. エンドレスサーキット - 唐 可可	108. ファンダメンタル - 唐 可可
109. Hoshizora Monologue - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	109. ノンフィクション!! - Liella!	109. だいすきのうた - 澁谷かのん	109. Dream Rainbow - Liella!	109. Jump Into the New World - Liella!	109. Stella! - 澁谷かのん、嵐 千砂都、平安名すみれ	109. Blooming Dance！Dance！ - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美
110. Within a Dream - Liella!	110. この街でいまキミと - Liella!	110. 勇気のカケラ - 嵐 千砂都	110. 探して！Future - Liella!	110. 名前呼びあうように - Liella!	110. Flyer’s High - 嵐 千砂都	110. Dancing Raspberry - 5yncri5e!
111. 未来の音が聴こえる - Liella!	111. Ringing! - 嵐 千砂都	111. 青空を待ってる - 澁谷かのん	111. TO BE CONTINUED - Liella!	111. 駆けるメリーゴーランド - 嵐 千砂都	111. 微熱のワルツ - 葉月 恋	111. ヒロインズ☆ランウェイ - 平安名すみれ
112. 水色のSunday - 唐 可可	112. Just woo!! - 平安名すみれ	112. 未来予報ハレルヤ！ - Liella!	112. Starry Prayer - 平安名すみれ	112. 君・街・空・星 - Liella!	112. 探して！Future - Liella!	112. 青空を待ってる - 澁谷かのん
113. ミッドナイトラプソディ - 葉月 恋	113. 青春HOPPERS - Liella!	113. Blooming Dance！Dance！ - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	113. 心キラララ - 澁谷かのん	113. パレードはいつも - 米女メイ	113. Including you - Liella!	113. GOING UP - Liella!
114. ファイティングコール - Liella!	114. Anniversary - 唐 可可	114. Summer Escape!! - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	114. バイバイしちゃえば！？ - Liella!	114. 変わらないすべて - 澁谷かのん、嵐 千砂都	114. Butterfly Wing - ウィーン・マルガレーテ	114. てくてく日和 - 桜小路きな子
115. この街でいまキミと - Liella!	115. Till Sunrise - Sunny Passion	115. Shooting Voice!! - Liella!	115. Message - 平安名すみれ	115. Sing！Shine！Smile！ - Liella!	115. 瞬きの先へ - Liella!	115. 名前呼びあうように - Liella!
116. Rhythm - 嵐 千砂都	116. ルカ - ウィーン・マルガレーテ	116. バイバイしちゃえば！？ - Liella!	116. Welcome to 僕らのセカイ - Liella!	116. 笑顔のPromise - Liella!	116. Sky Linker - 米女メイ	116. 瞬きの先へ - Liella!
117. Sing！Shine！Smile！ - Liella!	117. Memories - 澁谷かのん	117. Time to go - Liella!	117. DAISUKI FULL POWER - Liella!	117. Hoshizora Monologue - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	117. HAPPY TO DO WA！ - 唐 可可、平安名すみれ、葉月 恋	117. トゥ トゥ トゥ！ - Liella!
118. あふれる言葉 - 桜小路きな子	118. Blooming Dance！Dance！ - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	118. Departure - Liella!	118. 水色のSunday - 唐 可可	118. ファイティングコール - Liella!	118. dolce - ウィーン・マルガレーテ	118. リバーブ - 葉月 恋
119. 水しぶきのサイン - Liella!	119. 水色のSunday - 唐 可可	119. Go!! リスタート - Liella!	119. ユートピアマジック - Liella!	119. Dancing Heart La-Pa-Pa-Pa! - Liella!	119. ほんのちょっぴり - 澁谷かのん	119. 迷宮讃歌 - 葉月 恋
120. Departure - Liella!	120. ディストーション - CatChu!	120. ユニゾン - Liella!	120. Dancing Heart La-Pa-Pa-Pa! - Liella!	120. 罪DA・YO・NE - 米女メイ、若菜四季	120. あふれる言葉 - 桜小路きな子	120. Dreamer Coaster - 澁谷かのん
121. てくてく日和 - 桜小路きな子	121. Day1 - Liella!	121. 駆けるメリーゴーランド - 嵐 千砂都	121. 色づいて透明 - Liella!	121. Message - 平安名すみれ	121. ヒロインズ☆ランウェイ - 平安名すみれ	121. Summer Escape!! - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美
122. ビギナーズRock!! - 桜小路きな子	122. ベロア - KALEIDOSCORE	122. FANTASTiC - Liella!	122. Dreaming Energy - Liella!	122. High！モチベーション - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美、ウィーン・マルガレーテ、鬼塚冬毬	122. てくてく日和 - 桜小路きな子	122. 君を想う花になる - 嵐 千砂都
123. Till Sunrise - Sunny Passion	123. 水しぶきのサイン - Liella!	123. Dears - 葉月 恋	123. ひとひらだけ - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	123. Wish Song - Liella!	123. グソクムシのうた - 平安名すみれ	123. ほんのちょっぴり - 澁谷かのん
124. 名前呼びあうように - Liella!	124. Sky Linker - 米女メイ	124. みてろ！ - 平安名すみれ	124. Go!! リスタート - Liella!	124. プライム・アドベンチャー - Liella!	124. ルカ - ウィーン・マルガレーテ	124. 微熱のワルツ - 葉月 恋
125. パステルコラージュ - 鬼塚夏美	125. Departure - Liella!	125. Dancing Heart La-Pa-Pa-Pa! - Liella!	125. HAPPY TO DO WA！ - 唐 可可、平安名すみれ、葉月 恋	125. ユートピアマジック - Liella!	125. Primary - Liella!	125. 水色のSunday - 唐 可可
126. ユニゾン - Liella!	126. 微熱のワルツ - 葉月 恋	126. ユートピアマジック - Liella!	126. みてろ！ - 平安名すみれ	126. UNIVERSE!! - Liella!	126. ユートピアマジック - Liella!	126. Let's be ONE - Liella!
127. だいすきのうた - 澁谷かのん	127. Within a Dream - Liella!	127. 微熱のワルツ - 葉月 恋	127. あふれる言葉 - 桜小路きな子	127. Dreamer Coaster - 澁谷かのん	127. Rhythm - 嵐 千砂都	127. シェキラ☆☆☆ - Liella!
128. ワイルドカード - 鬼塚冬毬	128. 変わらないすべて - 澁谷かのん、嵐 千砂都	128. 心キラララ - 澁谷かのん	128. dolce - ウィーン・マルガレーテ	128. GOING UP - Liella!	128. ビギナーズRock!! - 桜小路きな子	128. Departure - Liella!
129. 結び葉 - 葉月 恋	129. Time to go - Liella!	129. Dreamer Coaster - 澁谷かのん	129. 駆けるメリーゴーランド - 嵐 千砂都	129. Sky Linker - 米女メイ	129. Time to go - Liella!	129. Anniversary - 唐 可可
130. パレードはいつも - 米女メイ	130. HOT PASSION!! - Sunny Passion	130. GOING UP - Liella!	130. パレードはいつも - 米女メイ	130. Including you - Liella!	130. Let's be ONE - Liella!	130. Primary - Liella!
131. 変わらないすべて - 澁谷かのん、嵐 千砂都	131. 影遊び - CatChu!	131. 1.2.3！ - Liella!	131. ティーンエイジ・ロンリネス - 唐 可可、平安名すみれ、桜小路きな子、鬼塚冬毬	131. 水しぶきのサイン - Liella!	131. みてろ！ - 平安名すみれ	131. 11th moon - ウィーン・マルガレーテ、鬼塚冬毬
132. Butterfly Wing - ウィーン・マルガレーテ	132. プライム・アドベンチャー - Liella!	132. Stella! - 澁谷かのん、嵐 千砂都、平安名すみれ	132. ミッドナイトラプソディ - 葉月 恋	132. スター宣言 - Liella!	132. 駆けるメリーゴーランド - 嵐 千砂都	132. dolce - ウィーン・マルガレーテ
133. 駆けるメリーゴーランド - 嵐 千砂都	133. MIRACLE NEW STORY - Liella!	133. Ringing! - 嵐 千砂都	133. 名前呼びあうように - Liella!	133. 色づいて透明 - Liella!	133. パレードはいつも - 米女メイ	133. Shooting Voice!! - Liella!
134. Primary - Liella!	134. 11th moon - ウィーン・マルガレーテ、鬼塚冬毬	134. Dream Rainbow - Liella!	134. 変わらないすべて - 澁谷かのん、嵐 千砂都	134. Shooting Voice!! - Liella!	134. Dreamer Coaster - 澁谷かのん	134. エンドレスサーキット - 唐 可可
135. リバーブ - 葉月 恋	135. Dreamer Coaster - 澁谷かのん	135. 変わらないすべて - 澁谷かのん、嵐 千砂都	135. Time to go - Liella!	135. Go!! リスタート - Liella!	135. リバーブ - 葉月 恋	135. Ringing! - 嵐 千砂都
136. ほんのちょっぴり - 澁谷かのん	136. Including you - Liella!	136. この街でいまキミと - Liella!	136. POP TALKING - Liella!	136. オレンジのままで - Liella!	136. Anniversary - 唐 可可	136. Message - 平安名すみれ
137. GOING UP - Liella!	137. トゥ トゥ トゥ！ - Liella!	137. 色づいて透明 - Liella!	137. エンドレスサーキット - 唐 可可	137. ビギナーズRock!! - 桜小路きな子	137. Departure - Liella!	137. 駆けるメリーゴーランド - 嵐 千砂都
138. トゥ トゥ トゥ！ - Liella!	138. HAPPY TO DO WA！ - 唐 可可、平安名すみれ、葉月 恋	138. だから僕らは鳴らすんだ！ - Liella!	138. 迷宮讃歌 - 葉月 恋	138. Till Sunrise - Sunny Passion	138. ベロア - KALEIDOSCORE	138. Dears - 葉月 恋
139. Including you - Liella!	139. FANTASTiC - Liella!	139. 君を想う花になる - 嵐 千砂都	139. リバーブ - 葉月 恋	139. エンドレスサーキット - 唐 可可	139. HOT PASSION!! - Sunny Passion	139. Memories - 澁谷かのん
140. Time to go - Liella!	140. だいすきのうた - 澁谷かのん	140. トゥ トゥ トゥ！ - Liella!	140. Ringing! - 嵐 千砂都	140. Stella! - 澁谷かのん、嵐 千砂都、平安名すみれ	140. 想われマリオネット - 澁谷かのん、嵐 千砂都、葉月 恋、鬼塚夏美、ウィーン・マルガレーテ	140. パレードはいつも - 米女メイ
141. オレンジのままで - Liella!	141. POP TALKING - Liella!	141. Flyer’s High - 嵐 千砂都	141. Dreamer Coaster - 澁谷かのん	141. 未来の音が聴こえる - Liella!	141. Till Sunrise - Sunny Passion	141. ひとひらだけ - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋
142. ひとひらだけ - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	142. QUESTION99 - Liella!	142. Free Flight - 澁谷かのん	142. Summer Escape!! - 桜小路きな子、米女メイ、若菜四季、鬼塚夏美	142. TO BE CONTINUED - Liella!	142. 変わらないすべて - 澁谷かのん、嵐 千砂都	142. Time to go - Liella!
143. グソクムシのうた - 平安名すみれ	143. Let's be ONE - Liella!	143. 迷宮讃歌 - 葉月 恋	143. グソクムシのうた - 平安名すみれ	143. HOT PASSION!! - Sunny Passion	143. Dears - 葉月 恋	143. 結ぶメロディ - Liella!
144. 瞬きの先へ - Liella!	144. dolce - ウィーン・マルガレーテ	144. グソクムシのうた - 平安名すみれ	144. トゥ トゥ トゥ！ - Liella!	144. Welcome to 僕らのセカイ - Liella!	144. Dreaming Energy - Liella!	144. グソクムシのうた - 平安名すみれ
145. 君を想う花になる - 嵐 千砂都	145. あふれる言葉 - 桜小路きな子	145. エンドレスサーキット - 唐 可可	145. HOT PASSION!! - Sunny Passion	145. Free Flight - 澁谷かのん	145. Ringing! - 嵐 千砂都	145. あふれる言葉 - 桜小路きな子
146. Flyer’s High - 嵐 千砂都	146. ひとひらだけ - 澁谷かのん、唐 可可、嵐 千砂都、平安名すみれ、葉月 恋	146. Till Sunrise - Sunny Passion	146. プライム・アドベンチャー - Liella!	146. あふれる言葉 - 桜小路きな子	146. Memories - 澁谷かのん	146. プライム・アドベンチャー - Liella!
147. 心キラララ - 澁谷かのん	147. Free Flight - 澁谷かのん	147. HOT PASSION!! - Sunny Passion	147. だいすきのうた - 澁谷かのん	147. てくてく日和 - 桜小路きな子	147. Message - 平安名すみれ	147. だいすきのうた - 澁谷かのん
"""

def ingest_data():
    print("🧹 Cleaning data and preparing users...")
    
    # Split raw text into lines and handle tabs
    lines = RAW_DATA.strip().split('\n')
    headers = lines[0].split('\t')
    rank_rows = lines[1:]

    # Build individual ranking lists for each user
    user_rankings = {h: [] for h in headers}
    
    for row in rank_rows:
        cols = row.split('\t')
        for i, col_val in enumerate(cols):
            if i < len(headers):
                user_rankings[headers[i]].append(col_val.strip())


    with httpx.Client(timeout=30.0) as client:
        for username, songs in user_rankings.items():
            # CLEAN THE INPUT: Fix the curly quote character globally
            cleaned_songs = [s.replace('’', "'") for s in songs]
            
            payload = {
                "username": username,
                "franchise": FRANCHISE,
                "subgroup_name": SUBGROUP,
                "ranking_list": "\n".join(cleaned_songs) # Use cleaned list
            }
            
            resp = client.post(f"{BASE_URL}/submit", json=payload)
            if resp.status_code == 200:
                print(f"   ✅ Success: {resp.json()['parsed_count']} songs parsed.")
            else:
                print(f"   ❌ Error: {resp.text}")

        # Trigger Recomputation
        print("\n⚙️  Triggering analysis recomputation...")
        trigger = client.post(f"{BASE_URL}/analysis/trigger")
        print(f"   Status: {trigger.json()['message']}")

if __name__ == "__main__":
    ingest_data()