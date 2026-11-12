Labirint **n × m** o'lchamli to'r ko'rinishida berilgan. Har bir katak quyidagilardan biri:

- `.` — bo'sh katak,
- `#` — devor (o'tib bo'lmaydi),
- `S` — boshlang'ich katak (aniq bitta),
- `F` — chiqish (aniq bitta).

Bir qadamda qo'shni katakka (yuqori, past, chap yoki o'ng) o'tish mumkin. `S` dan `F` ga yetib borish uchun **eng kam** qadamlar sonini toping. Agar yetib borishning iloji bo'lmasa, **−1** chiqaring.

### Kiruvchi ma'lumotlar
Birinchi qatorda **n** va **m** (1 ≤ n, m ≤ 1000, n·m ≥ 2).
Keyingi **n** ta qatorning har birida uzunligi **m** ga teng satr — labirint qatorlari.

### Chiquvchi ma'lumotlar
Bitta son — eng kam qadamlar soni yoki −1.

### Izoh
Bu masala **kenglik bo'yicha qidiruv (BFS)** algoritmiga mo'ljallangan. Barcha yo'llarni chuqurlik bo'yicha sanab chiqish katta labirintlarda juda sekin ishlaydi.
