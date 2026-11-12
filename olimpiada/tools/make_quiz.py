"""Test savollarini quiz/questions.json fayliga yozadi.
Turlar: single (bitta javob), multi (bir nechta javob), text (qisqa javob),
order (tartiblash, drag&drop), match (moslashtirish)."""
import json, os

Q = []
def add(**k): k.setdefault("points", 4); Q.append(k)

add(type="single", text="Saralangan massivda binar qidiruvning eng yomon holatdagi vaqt murakkabligi qanday?",
    options=["O(n)", "O(log n)", "O(n log n)", "O(1)"], answer=1)
add(type="single", text="Quyidagi kod fragmentining vaqt murakkabligi qanday?",
    code="for (int i = 1; i < n; i *= 2)\n    for (int j = 0; j < n; j++)\n        s++;",
    options=["O(n²)", "O(n log n)", "O(log n)", "O(n)"], answer=1)
add(type="text", text="Quyidagi funksiya uchun f(5) qiymati nechaga teng?",
    code="int f(int n) {\n    if (n <= 1) return 1;\n    return f(n - 1) + f(n - 2);\n}", answer=["8"])
add(type="order", text="Murakkablik sinflarini **o'sish tartibida** joylashtiring (eng tezi tepada). Elementlarni sichqoncha bilan suring yoki ↑ ↓ tugmalaridan foydalaning.",
    items=["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(2ⁿ)"])
add(type="multi", text="Quyidagi saralash algoritmlaridan qaysilari **barqaror** (stable)? Barcha to'g'ri javoblarni belgilang.",
    options=["Merge sort", "Insertion sort", "Quick sort (odatiy amalga oshirish)", "Heap sort", "Bubble sort"], answer=[0, 1, 4])
add(type="single", text="Quick sort algoritmining **eng yomon** holatdagi vaqt murakkabligi qanday?",
    options=["O(n log n)", "O(n²)", "O(n)", "O(log n)"], answer=1)
add(type="match", text="Har bir algoritmni uning (o'rtacha holatdagi) vaqt murakkabligi bilan moslashtiring.",
    left=["Merge sort", "Binar qidiruv", "Chiziqli qidiruv", "Pufakchali saralash (bubble sort)"],
    right=["O(log n)", "O(n)", "O(n log n)", "O(n²)", "O(1)"], answer=[2, 0, 1, 3])
add(type="single", text="T(n) = 2·T(n/2) + n rekurrent munosabatining yechimi qanday (Master teoremasi)?",
    options=["Θ(n)", "Θ(n log n)", "Θ(n²)", "Θ(log n)"], answer=1)
add(type="single", text="Quyidagilardan qaysi biri **«bo'l va hukmronlik qil»** (divide and conquer) usuliga misol **emas**?",
    options=["Merge sort", "Quick sort", "Binar qidiruv", "Deykstra algoritmi"], answer=3)
add(type="text", text="[3, 8, 1, 9, 4] massiviga **insertion sort** qo'llanmoqda. Tashqi siklning 2-iteratsiyasidan keyin (ya'ni 2- va 3-elementlar o'z joyiga qo'yilgach) massiv qanday ko'rinishda bo'ladi? Sonlarni probel bilan yozing.",
    answer=["1 3 8 9 4"])
add(type="single", text="Qaysi masalada **ochko'z (greedy)** algoritm har doim optimal javob beradi?",
    options=["Ixtiyoriy tangalar to'plami bilan qaytimni eng kam tanga bilan berish", "0/1 ryukzak masalasi",
             "Kasrli (fractional) ryukzak masalasi", "Grafda eng uzun oddiy yo'lni topish"], answer=2)
add(type="single", text="n-Fibonachchi sonini **memoizatsiya** (yodlab qolish) bilan rekursiv hisoblashning vaqt murakkabligi qanday?",
    options=["O(2ⁿ)", "O(n)", "O(n²)", "O(log n)"], answer=1)
add(type="text", text="0/1 ryukzak: sig'im W = 5. Narsalar (og'irlik, qiymat): (2, 3), (3, 4), (4, 5), (5, 6). Erishish mumkin bo'lgan **maksimal umumiy qiymat** nechaga teng?",
    answer=["7"])
add(type="text", text="\"ABCBDAB\" va \"BDCABA\" satrlarining **eng uzun umumiy qism ketma-ketligi** (LCS) uzunligi nechaga teng?",
    answer=["4"])
add(type="single", text="Kenglik bo'yicha qidiruv (BFS) qaysi ma'lumotlar tuzilmasidan foydalanadi?",
    options=["Stek", "Navbat", "Uyum (heap)", "Hesh-jadval"], answer=1)
GRAPH = "A: B, D\nB: A, E\nC: D, F\nD: A, C\nE: B, F\nF: C, E"
add(type="order", text="Yo'naltirilmagan graf qo'shnilik ro'yxati bilan berilgan (qo'shnilar alifbo tartibida ko'rib chiqiladi). **A** uchidan boshlangan **BFS** uchlarni qanday tartibda ko'radi? Uchlarni shu tartibda joylashtiring.",
    code=GRAPH, items=["A", "B", "D", "E", "C", "F"])
add(type="text", text="Xuddi shu graf uchun **A** uchidan boshlangan rekursiv **DFS** uchlarni qanday tartibda ko'radi (qo'shnilar alifbo tartibida)? Harflarni probel bilan yozing.",
    code=GRAPH, answer=["A B E F C D"])
add(type="order", text="**Deykstra** algoritmi qadamlarini to'g'ri tartibda joylashtiring.",
    items=["Barcha uchlar masofasini ∞, boshlang'ich uch masofasini 0 qilish",
           "Boshlang'ich uchni ustuvor navbatga qo'shish",
           "Navbatdan masofasi eng kichik uchni olish",
           "Olingan uchning qo'shnilari uchun relaksatsiya qilish (masofani yangilash)",
           "Navbat bo'shaguncha oldingi ikki qadamni takrorlash"])
add(type="single", text="Deykstra algoritmi qaysi holatda **noto'g'ri** natija berishi mumkin?",
    options=["Grafda manfiy og'irlikli qirralar bo'lsa", "Graf yo'naltirilmagan bo'lsa",
             "Qirralar soni juda ko'p bo'lsa", "Graf daraxt bo'lsa"], answer=0)
add(type="text", text="Graf qirralari (uch–uch: og'irlik): A–B: 4, A–C: 1, B–C: 2, B–D: 5, C–D: 8, D–E: 3, C–E: 9. **Minimal karkas daraxt** (MST) og'irligi nechaga teng?",
    answer=["11"])
add(type="multi", text="Binar **min-uyum** (min-heap) amallarining murakkabligi to'g'ri ko'rsatilganlarini belgilang.",
    options=["Element qo'shish — O(log n)", "Minimumni ko'rish — O(1)", "Minimumni o'chirish — O(1)",
             "Ixtiyoriy elementni qidirish — O(log n)"], answer=[0, 1])
add(type="single", text="Hesh-jadvalda element qidirishning **o'rtacha** vaqt murakkabligi qanday?",
    options=["O(1)", "O(log n)", "O(n)", "O(n log n)"], answer=0)
add(type="text", text="Union-Find: 1 dan 6 gacha bo'lgan elementlarning har biri alohida to'plamda. Amallar: union(1, 2), union(3, 4), union(2, 4), union(5, 6). Oxirida **nechta** to'plam qoladi?",
    answer=["2"])
add(type="match", text="Har bir masalani uni yechish uchun eng mos algoritm bilan moslashtiring.",
    left=["Musbat og'irlikli grafda eng qisqa yo'l", "Minimal karkas daraxt", "Og'irliksiz grafda eng qisqa yo'l",
          "Saralangan massivda element qidirish"],
    right=["Deykstra", "Kruskal", "BFS", "Binar qidiruv", "Pufakchali saralash"], answer=[0, 1, 2, 3])
add(type="single", text="**Las-Vegas** turidagi tasodifiy (randomized) algoritmga qaysi ta'rif mos keladi?",
    options=["Har doim to'g'ri javob beradi, lekin ishlash vaqti tasodifiy", "Ishlash vaqti aniq, lekin javob faqat ma'lum ehtimol bilan to'g'ri",
             "Har doim xato javob beradi", "Faqat parallel kompyuterlarda ishlaydi"], answer=0)

for i, q in enumerate(Q, 1):
    q["id"] = i
assert len(Q) == 25 and sum(q["points"] for q in Q) == 100
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "quiz", "questions.json")
json.dump(Q, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(Q), "ta savol yozildi")
