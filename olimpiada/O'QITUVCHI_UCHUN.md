# O'qituvchi uchun: masalalar, yechim g'oyalari va kutilgan xatolar

Etalon yechimlar: `tools/solutions/` (C++ va Python). Barcha testlar ikkala yechim bilan tekshirilgan.

| # | Masala | Algoritm | Murakkablik | Talabalarning odatiy xatosi | Sodda yechim natijasi |
|---|---|---|---|---|---|
| A | Juft sonlar yig'indisi | Bir marta o'tish | O(n) | `int` da toshib ketish (yig'indi 10¹⁴ gacha); C++ da `x % 2 == 1` bilan manfiy toqlarni tekshirish | `int` bilan ≈ 50% |
| B | Palindrom | Ikki ko'rsatkich: s[i] va s[n−1−i] juftlarini solishtirish | O(n) | Barcha juftlarni ikki marta sanash (javob 2× bo'ladi) | — |
| C | Kitob do'koni | Saralash + `upper_bound` | O((n+q) log n) | Har so'rovda butun massivni ko'rish | O(n·q) ≈ 60% (katta testlarda TLE) |
| D | Eng foydali davr | Kadane: `cur = max(a[i], cur + a[i])` | O(n) | Hamma son manfiy bo'lsa 0 chiqarish; `int` toshishi | O(n²) ≈ 63% |
| E | Zinapoya | `dp[i] = dp[i−1] + dp[i−2] + dp[i−3]`, singan pog'onada `dp[i] = 0` | O(n) | Modulni unutish; rekursiya xotirasiz | Rekursiya — faqat kichik testlar |
| F | Ryukzak | 1 o'lchamli DP, `c` ni W dan pastga qarab aylanish | O(n·W) | `c` ni o'sish tartibida aylanish (har narsa bir necha marta olinadi); ochko'z (greedy) yondashuv | Greedy — WA; teskari yo'nalishli DP ≈ 30% |
| G | Labirint | BFS (navbat) | O(n·m) | DFS bilan barcha yo'llarni sanash; tashrifni belgilamaslik | DFS — TLE |
| H | Shaharlar | Deykstra + ustuvor navbat (min-heap) | O(m log n) | `int` masofa; Bellman–Ford O(n·m); "-1" holatini unutish | Bellman–Ford: maxsus zanjir testlarida TLE (≈ 85%) |

## Ball tizimi
Har bir masala uchun: `ball = masala_bali × (o'tgan testlar / jami testlar)`.
Jami: 1600 ball. Teng ballda — oxirgi ball olingan vaqti erta bo'lgan yuqorida.

## Tavsiya etilgan davomiylik
3 soat (180 daqiqa). Kuchli guruh uchun 2.5 soat, birinchi kurslar uchun A–F masalalari bilan 2 soat.

---

# Test (25 savol, har biri 4 ball)

To'liq kalit va har bir savol bo'yicha "necha foiz to'g'ri javob berdi" statistikasi: **Admin → Test kaliti va statistika**.

| # | Mavzu | Turi | Javob |
|---|---|---|---|
| 1 | Binar qidiruv murakkabligi | bitta javob | O(log n) |
| 2 | Ichma-ich sikl murakkabligi | bitta javob | O(n log n) |
| 3 | Rekursiya (f(5)) | qisqa javob | 8 |
| 4 | Murakkablik sinflarini tartiblash | **tartiblash** | O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2ⁿ) |
| 5 | Barqaror saralashlar | ko'p javob | Merge, Insertion, Bubble |
| 6 | Quick sort eng yomon holat | bitta javob | O(n²) |
| 7 | Algoritm ↔ murakkablik | **moslashtirish** | Merge–O(n log n), Binar–O(log n), Chiziqli–O(n), Bubble–O(n²) |
| 8 | Master teoremasi | bitta javob | Θ(n log n) |
| 9 | Bo'l va hukmronlik qil emas | bitta javob | Deykstra |
| 10 | Insertion sort qadami | qisqa javob | 1 3 8 9 4 |
| 11 | Greedy optimal | bitta javob | Kasrli ryukzak |
| 12 | Memoizatsiya | bitta javob | O(n) |
| 13 | 0/1 ryukzak | qisqa javob | 7 |
| 14 | LCS uzunligi | qisqa javob | 4 |
| 15 | BFS tuzilmasi | bitta javob | Navbat |
| 16 | BFS tartibi | **tartiblash** | A B D E C F |
| 17 | DFS tartibi | qisqa javob | A B E F C D |
| 18 | Deykstra qadamlari | **tartiblash** | (5 qadam, mantiqiy tartibda) |
| 19 | Deykstra cheklovi | bitta javob | Manfiy og'irliklar |
| 20 | MST og'irligi | qisqa javob | 11 |
| 21 | Min-heap amallari | ko'p javob | Qo'shish O(log n), Ko'rish O(1) |
| 22 | Hesh-jadval | bitta javob | O(1) |
| 23 | Union-Find | qisqa javob | 2 |
| 24 | Masala ↔ algoritm | **moslashtirish** | Deykstra, Kruskal, BFS, Binar qidiruv |
| 25 | Las-Vegas algoritmi | bitta javob | Javob doim to'g'ri, vaqt tasodifiy |

Hisoblanadigan javoblar (3, 10, 13, 14, 16, 17, 20) dastur bilan mustaqil tekshirilgan.
Qisqa javoblarda katta-kichik harf, vergul va qavslar hisobga olinmaydi ("[1, 3, 8, 9, 4]" ham qabul qilinadi).
