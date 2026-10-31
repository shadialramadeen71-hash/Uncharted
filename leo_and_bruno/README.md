# Leo & Bruno 🐻 — مسلسل كرتوني لـ YouTube Shorts

مسلسل كرتوني عن **ليو** (ولد صغير) و**برونو** (دب كبير وطيب) ومغامراتهم.
- كل حلقة **أقل من 15 ثانية**
- فيديو عمودي **1080×1920** (مقاس YouTube Shorts)، 30 إطار بالثانية، مع صوت
- الحوار **بالإنجليزي**، مع ترجمة على الشاشة تضيء فيها كل كلمة لما تنقال
- حركة الفم متزامنة مع الصوت، مع موسيقى خلفية ومؤثرات صوتية

## الحلقات الجاهزة للرفع (`output/`)

| # | الملف | المدة | القصة |
|---|------|------|-------|
| 1 | `ep01_the_honey_hunt.mp4` | 14.3s | برونو بده ياخذ عسل من الشجرة… والنحل بلحقهم! |
| 2 | `ep02_the_treasure_map.mp4` | 12.6s | خريطة كنز على البحر — والكنز طلع… كوكيز! |
| 3 | `ep03_the_snow_bear.mp4` | 13.4s | كرة ثلج عملاقة بتوقع على برونو وبصير "دب ثلج" |
| 4 | `ep04_mission_to_the_moon.mp4` | 11.6s | عد تنازلي 3-2-1 ورحلة صاروخ للقمر |
| 5 | `ep05_gone_fishing.mp4` | 12.5s | برونو بده سمكة كبيرة… بصطاد وحدة زغيرة وبترشه بالمي! |

## عناوين ووصف مقترح لليوتيوب

1. **Leo & Bruno 🐻 The Honey Hunt 🍯🐝 #shorts**
2. **Leo & Bruno 🐻 The Treasure Map 🏴‍☠️🍪 #shorts**
3. **Leo & Bruno 🐻 The Snow Bear ☃️ #shorts**
4. **Leo & Bruno 🐻 Mission to the Moon 🚀🌙 #shorts**
5. **Leo & Bruno 🐻 Gone Fishing 🎣🐟 #shorts**

الوصف:
```
Leo and his best friend Bruno the bear go on a tiny adventure! 🐻✨
New episode every week — subscribe for more!
#shorts #kidscartoon #cartoon #bear #kidsstories #learnenglish #animation
```
> عند الرفع اختار **"Made for kids" = Yes** (اليوتيوب بطلبها لمحتوى الأطفال).

## كيف تعمل حلقات جديدة بنفسك

المتطلبات: Python 3 و `ffmpeg` واتصال إنترنت (للأصوات).
```bash
pip install pycairo numpy edge-tts
cd leo_and_bruno
python3 render.py            # يعمل كل الحلقات في output/
python3 render.py 3          # الحلقة 3 بس
python3 render.py 2 --preview  # صورة معاينة للقطات في build/ بدون فيديو
```

لإضافة حلقة جديدة: افتح `episodes.py` واكتب حلقة جديدة زي الموجودين:
- `beats`: قائمة جُمل (`say=("leo"|"bruno", "text")`) أو حركات (`act=..., dur=ثواني`) مع مؤثرات `sfx`
- `draw_epN(ctx, T, tl)`: دالة بترسم المشهد بالوقت T
- وبعدين ضيفها لقائمة `EPISODES`. البرنامج بوقف ويعطي خطأ إذا الحلقة صارت أطول من 15 ثانية.

الملفات:
- `draw.py` — رسم الشخصيات (ليو، برونو) والخلفيات (غابة، بحر، ثلج، ليل، نهر) والأغراض
- `audio.py` — الأصوات (Microsoft Edge neural voices) والموسيقى والمؤثرات
- `episodes.py` — سيناريو الحلقات
- `render.py` — الترجمة، تزامن الفم، دمج الصوت، وتصدير MP4
