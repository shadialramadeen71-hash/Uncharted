# Brick Heroes ABC 🦸‍♂️🧱 — مسلسل تعليم الحروف الإنجليزية (YouTube Shorts)

مسلسل كامل من **26 حلقة** (حلقة لكل حرف A → Z)، كل حلقة **14.5 ثانية**،
بمقاس شورتس العمودي **1080×1920**. الشخصيات أبطال خارقين بشكل قطع المكعّبات،
وكل شيء — الرسم، الحركة، الموسيقى، والصوت — مصنوع بالكود.

## الفيديوهات الجاهزة
موجودة في مجلد [`output/`](output/) من `01_A_Apple.mp4` إلى `26_Z_Zebra.mp4`.
العناوين والوصف والهاشتاقات لكل حلقة في [`YOUTUBE_METADATA.md`](YOUTUBE_METADATA.md).

## هيكل كل حلقة (على إيقاع 120 BPM)
| الوقت | المشهد | الصوت |
|---|---|---|
| 0–2 ث | البطل يطير للشاشة + عنوان BRICK HEROES ABC | "Brick Heroes!" |
| 2–6 ث | الحرف يُبنى قطعة قطعة من المكعّبات | "Letter A!  A, A, A!" |
| 6–10 ث | الكلمة + صورتها (Apple 🍎) | "A is for Apple! Apple! Apple!" |
| 10–12.75 ث | الحرف الكبير والصغير A a | "Big A, little a!" |
| 12.75–14.5 ث | بطاقة الحلقة الجاية NEXT: B | "Next is B!" |

## فريق الأبطال (شخصيات أصلية)
Captain Spark 🔴 · Blue Bolt 🔵 · Star Girl 🩷 · Green Guardian 🟢 · Turbo Tiger 🟠 · Night Brick 🟣
— على صدر كل بطل حرف الحلقة.

## الألحان (مولّدة بالكود)
ألحان أطفال تقليدية من التراث العام (Public Domain) تتبدّل بين الحلقات:
Twinkle Twinkle / ABC Song · Mary Had a Little Lamb · London Bridge · Old MacDonald · Frère Jacques · Yankee Doodle.
النوتات مكتوبة في `episodes.py`، و`audio.py` يولّد صوت "بيانو ألعاب" + باص + طبول
بالـ numpy، ثم يضيف صوت الراوي (espeak-ng/mbrola) ويخفض الموسيقى تحت الكلام تلقائياً.

## إعادة التوليد / التعديل
```bash
sudo apt-get install -y ffmpeg espeak-ng mbrola mbrola-us1 fonts-noto-color-emoji fonts-inter
pip install numpy pillow
python3 render.py          # كل الحلقات (~3 دقائق)
python3 render.py A B C    # حروف محددة
```
- غيّر الكلمات/الإيموجي في `LETTERS` داخل `episodes.py`
- غيّر الأبطال وألوانهم في `HEROES`
- أضف لحن جديد في `TUNES` (صيغة: `C5 D5 E5:2` = نوتة:عدد النبضات)

> ملاحظة: الشخصيات بأسلوب "قطع المكعّبات" لكنها أصلية وغير مرتبطة بعلامة LEGO® أو أي أبطال
> محميين بحقوق نشر، عشان القناة تكون آمنة من مشاكل الحقوق. لا تكتب كلمة "LEGO" في العنوان.
