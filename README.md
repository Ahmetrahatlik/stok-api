# Stok API

Küçük bir hırdavat dükkânı için stok, satış ve veresiye takibi yapan REST API.
FastAPI, PostgreSQL ve Docker ile yazıldı; her yüklemede GitHub Actions testleri PostgreSQL üzerinde çalıştırır.

*A REST API for stock, sales and customer credit tracking in a small hardware shop. Built with FastAPI, PostgreSQL and Docker; GitHub Actions runs the tests against PostgreSQL on every push. English summary below.*

![CI](https://github.com/Ahmetrahatlik/stok-api/actions/workflows/ci.yml/badge.svg)

**Canlı demo:** https://stok-api-demo.onrender.com (açılan sayfadan istekleri deneyebilirsiniz; ücretsiz sunucu uykudaysa ilk açılış ~50 sn sürer, veriler yeniden başlatmada sıfırlanır). Veri değiştirmek için "Authorize" düğmesinden `demo` / `demo1234` ile giriş yapın.
*Live demo with sample data: open the link and use the interactive docs.*

**Web paneli:** https://stok-panel-7p4r.onrender.com ([kaynak kodu](https://github.com/Ahmetrahatlik/stok-panel)), bu API'yi kullanan React + TypeScript arayüzü.

## Neden?

Bir hırdavat dükkânı için internetsiz çalışan bir masaüstü stok programı geliştirdim. Bu proje aynı iş kurallarını sunucu tarafında, çok kullanıcılı bir API olarak yeniden kuruyor.

## Özellikler

- **Ürünler:** ekleme, güncelleme, arama, kritik stok listesi
- **Stok hareketleri:** mal girişi (alış fiyatı güncellenir), sayım düzeltmesi, hareket geçmişi
- **Satış:** birden çok kalem, nakit veya veresiye; stok yetmezse satışın tamamı iptal olur
- **Veresiye:** müşteri borcu, tahsilat, borçlu müşteriler listesi
- **Giriş (JWT):** okumak herkese açık; ürün ekleme, mal girişi, satış ve tahsilat gibi veriyi değiştiren her işlem `/auth/token` ile alınan token ister. Şifreler bcrypt ile saklanır.
- **Veritabanı göçleri (Alembic):** tablolar `alembic upgrade head` ile kurulur; bir test, göçlerin modellerle birebir aynı olduğunu her seferinde kontrol eder.
- **Rapor:** tarih aralığına göre ciro, maliyet, brüt kâr ve toplam alacak

## Önemli kararlar

- **Eşzamanlı satışlar:** Satış sırasında ürün satırları `SELECT ... FOR UPDATE` ile kilitlenir. Kilitler ürün kimliği sırasıyla alındığı için iki satış birbirini kilitleyemez (deadlock).
- **Ya hep ya hiç:** Satıştaki kalemlerden biri bile stoğu aşarsa hiçbir stok düşmez; API hangi ürünün yetmediğini söyler.
- **Fiyat geçmişi korunur:** Satış kalemine o anki satış ve alış fiyatı yazılır. Ürün fiyatı sonradan değişse de eski satışların kârı doğru hesaplanır.
- **Para hesabı:** Tutarlar `Decimal` ve veritabanında `NUMERIC` olarak tutulur; ondalık yuvarlama hatası olmaz.
- **Veritabanı kuralı:** Stok veritabanı düzeyinde de eksiye düşemez (`CHECK stock >= 0`).
- **Türkçe arama:** SQL'in `LOWER`/`ILIKE` işlemleri İ, I ve Ç harflerinde güvenilir değil ("çek" araması "Çekiç"i bulmuyordu). Ürün adının Türkçe kurallarla küçültülmüş hâli ayrı bir sütunda tutuluyor ve arama orada yapılıyor.

## Çalıştırma

Docker ile (API + PostgreSQL):

```bash
docker compose up --build
```

API dokümantasyonu: http://localhost:8000/docs

Docker olmadan (SQLite ile):

```bash
python -m venv .venv
.venv/Scripts/activate        # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
ADMIN_USERNAME=admin ADMIN_PASSWORD=admin1234 uvicorn app.main:app --reload
```

## Testler

```bash
pytest -q
```

Yerelde testler bellekte çalışan SQLite kullanır. CI'da `DATABASE_URL` PostgreSQL'i gösterir, aynı testler gerçek veritabanında çalışır.

## Örnek istekler

```bash
# Giriş yap ve token'ı sakla
TOKEN=$(curl -s -X POST localhost:8000/auth/token -d "username=admin&password=admin1234" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"

# Ürün ekle
curl -X POST localhost:8000/products -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"name": "Çekiç", "purchase_price": "80", "sale_price": "120", "min_stock": "5"}'

# 10 adet mal girişi
curl -X POST localhost:8000/stock/purchases -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": "10"}'

# Müşteri ekle ve veresiye satış yap
curl -X POST localhost:8000/customers -H "$AUTH" -H "Content-Type: application/json" -d '{"name": "Mehmet Usta"}'
curl -X POST localhost:8000/sales -H "$AUTH" -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": "2"}], "payment_type": "credit", "customer_id": 1}'

# Kâr raporu
curl localhost:8000/reports/profit
```

## Proje yapısı

```
app/
  main.py          uygulama ve router kayıtları
  db.py            veritabanı bağlantısı
  models.py        SQLAlchemy tabloları
  schemas.py       Pydantic giriş/çıkış şemaları
  routers/         products, stock, customers, sales
tests/             pytest testleri
```

## Geliştirme süreci

Proje, Claude Code ile yapay zekâ destekli geliştirildi. İş kurallarını ve kabul kriterlerini ben belirledim, kod ajanla yazıldı ve her davranış otomatik testlerle doğrulandı.

---

## English summary

- **Endpoints:** products, stock purchases and count adjustments, multi-line cash or credit sales, customer payments, and a profit report.
- **Concurrency:** product rows are locked with `SELECT ... FOR UPDATE` in id order, so concurrent sales cannot oversell or deadlock.
- **Atomic sales:** if any line exceeds stock, nothing is sold and the API lists the short items.
- **Correct history:** each sale line stores the price and cost at the time of sale.
- **Money:** `Decimal` / `NUMERIC`, plus a database `CHECK` that stock never goes negative.
- **Run:** `docker compose up --build`, then open http://localhost:8000/docs. Tests: `pytest -q`.
- Built with AI assistance (Claude Code); requirements and acceptance criteria are mine, and behaviour is verified by automated tests.
