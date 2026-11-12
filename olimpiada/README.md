# Algoritmlarni loyihalash — onlayn olimpiada tizimi

Talabalar ro'yxatdan o'tadi va ikki bo'limni **istalgan tartibda** bajaradi:

| Bo'lim | Tarkibi | Vaqt (standart) | Ball |
|---|---|---|---|
| **Test** | 25 savol: bitta/ko'p javobli, qisqa javob, **interaktiv** (tartiblash drag&drop, moslashtirish) | 30 daqiqa | 100 |
| **Masalalar** | 8 masala osondan qiyinga (A–H), C++17 / Python 3, avtomatik tekshiruv | 120 daqiqa | 1600 |

- Bo'lim boshlanganda talabaning **shaxsiy taymeri** ishga tushadi; vaqt tugasa bo'lim avtomatik yopiladi.
- Bir vaqtda faqat bitta bo'lim ochiq bo'ladi.
- **3 ta reyting:** Test, Masalalar, Umumiy (test 40% + masalalar 60%, admin o'zgartiradi).
- **Halollik nazorati:** to'liq ekran (test), boshqa tab/dasturga o'tish, nusxalash/joylash qayd etiladi;
  savollar va variantlar har bir talabada boshqacha tartibda; o'xshash kodlarni topish; IP jurnali.
- Admin: vaqtlarni sozlash, talabaga qo'shimcha vaqt berish, urinishni bekor qilish, test kaliti va
  har bir savol statistikasi, natijalarni Excel (CSV) ga yuklash.

## Tuzilishi
```
olimpiada/
├── app.py                 # Veb-sayt (Flask)
├── judge.py               # Kodni avtomatik tekshiruvchi
├── quiz/questions.json    # 25 ta test savoli va JAVOBLARI
├── problems/A..H/         # Masalalar: shart, limitlar, testlar
├── templates/, static/    # Sahifalar, dizayn, guard.js (nazorat)
├── tools/                 # make_quiz.py, gen_tests.py, etalon yechimlar
└── data/                  # SQLite baza (avtomatik yaratiladi, GitHub'ga yuklanmaydi)
```

---

## 1. Kompyuterda sinab ko'rish (Kubuntu)
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip g++ unzip
cd ~/olimpiada
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
SECRET_KEY="uzun-tasodifiy-satr" ADMIN_PASSWORD="Parol123" python3 app.py
```
Brauzer: `http://localhost:5000` → admin: `admin` / `Parol123`.
Boshqa brauzer oynasida (inkognito) talaba sifatida ro'yxatdan o'tib, bo'limlarni sinab ko'ring.

## 2. GitHub'ga yuklash (FAQAT PRIVATE!)
> GitHub kodni **saqlaydi**, lekin saytni **ishga tushirmaydi** (GitHub Pages Python va kod
> tekshiruvchini ishlata olmaydi). Repo **Private** bo'lishi shart: unda test javoblari
> (`quiz/questions.json`) va masalalar testlari bor.

```bash
cd ~/olimpiada
git init
git add .
git commit -m "Olimpiada tizimi"
sudo apt install -y gh
gh auth login
gh repo create olimpiada --private --source=. --push
```
Keyingi o'zgarishlarni yuklash: `git add . && git commit -m "o'zgarish" && git push`

## 3. olimpiada.sigmelle.com da ishga tushirish

### A-variant: VPS server (tavsiya etiladi)
Kerak: Ubuntu VPS (2 CPU, 2–4 GB RAM). Domen DNS sozlamalarida yozuv qo'shing:
`A` turi · nomi `olimpiada` · qiymati `SERVER_IP`.

Serverda:
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo apt install -y git caddy gh
gh auth login
gh repo clone olimpiada
cd olimpiada
sed -i 's/"80:5000"/"127.0.0.1:5000:5000"/' docker-compose.yml
nano docker-compose.yml          # SECRET_KEY va ADMIN_PASSWORD ni o'zgartiring
sudo docker compose up -d --build

echo 'olimpiada.sigmelle.com {
    reverse_proxy 127.0.0.1:5000
}' | sudo tee /etc/caddy/Caddyfile
sudo systemctl restart caddy
```
Sayt: `https://olimpiada.sigmelle.com` (SSL sertifikatni Caddy o'zi oladi).
Yangilash: `cd ~/olimpiada && git pull && sudo docker compose up -d --build`

### B-variant: o'z noutbukingizdan Cloudflare Tunnel orqali (bepul)
Shart: sigmelle.com domeni Cloudflare'ga ulangan bo'lishi (nameserver'lar Cloudflare'niki).
Olimpiada davomida noutbuk yoqiq, zaryadda va internetga ulangan turishi kerak.
```bash
curl -L -o cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
cloudflared tunnel login
cloudflared tunnel create olimpiada
cloudflared tunnel route dns olimpiada olimpiada.sigmelle.com

# 1-terminal: sayt
cd ~/olimpiada && source venv/bin/activate
export SECRET_KEY="uzun-tasodifiy-satr" ADMIN_PASSWORD="Parol123" TZ=Asia/Tashkent
gunicorn -w 1 --threads 16 -b 127.0.0.1:5000 app:app

# 2-terminal: tunnel
cloudflared tunnel run --url http://localhost:5000 olimpiada
```

> Ikkala variantda ham `SECRET_KEY` ni bir marta belgilang va o'zgartirmang (aks holda server
> qayta ishga tushganda hamma tizimdan chiqib ketadi). `-w 1` ni o'zgartirmang.

---

## Olimpiada kuni
1. **Admin → Olimpiada sozlamalari:** oyna (masalan 09:00–13:00), test va masalalar davomiyligi,
   umumiy reyting ulushlari, nazorat sozlamalari.
2. Talabalarga manzilni bering: ro'yxatdan o'tadi → bosh sahifada **Test** yoki **Masalalar** → **Boshlash**.
3. Admin sahifasida har bir talabaning holati (faol / yakunlangan) va qoidabuzarliklar soni ko'rinadi;
   ustiga bosib batafsil jurnalni (vaqt, hodisa, IP) ko'rasiz.
4. Texnik muammo bo'lsa: talabaga **+ daqiqa** qo'shing (yakunlangan bo'lsa qayta ochiladi)
   yoki **Bekor** — bo'limni qaytadan boshlashga ruxsat.
5. Tugagach: **Natijalar (CSV)**, **O'xshash yechimlar**, **Test kaliti va statistika**.
   Test bo'yicha to'g'ri javoblar talabalarga oyna tugagandan keyin ochiladi.

## Internetdan foydalanishni cheklash haqida
Brauzer ichidagi nazorat **qoidabuzarlikni aniqlaydi va qayd etadi**, lekin to'liq to'xtata olmaydi
(talaba telefon yoki ikkinchi kompyuterdan foydalanishi mumkin). Eng ishonchli yo'l:
1. Olimpiadani **kompyuter sinfida, nazoratchi bilan** o'tkazish.
2. Sinf routerida/firewall'da faqat `olimpiada.sigmelle.com` ga ruxsat berish (oq ro'yxat).
3. Telefonlarni yig'ib olish.
4. Masalalarda talabalar kodni faqat saytda yozsa, admin sozlamalarida "Masalalarda nazorat" va
   "Kod joylashni taqiqlash"ni yoqing ("Namunada sinash" tugmasi borligi uchun bu qulay).
5. Shubhali natijalarni og'zaki savol bilan tekshirish.

## Savol yoki masalani o'zgartirish
- **Test:** `tools/make_quiz.py` ni tahrirlang → `python3 tools/make_quiz.py` (quiz/questions.json yangilanadi).
- **Masala:** `problems/<ID>/` (meta.json, statement.md, tests/). Testlarni qayta yaratish: `python3 tools/gen_tests.py`.
- O'zgarishdan keyin saytni qayta ishga tushiring.
