# Stok API

Küçük bir hırdavat dükkânı için stok, satış ve veresiye takibi yapan REST API.
FastAPI, PostgreSQL ve Docker ile yazıldı; her yüklemede GitHub Actions testleri PostgreSQL üzerinde çalıştırır.

*A REST API for stock, sales and customer credit tracking in a small hardware shop. Built with FastAPI, PostgreSQL and Docker; GitHub Actions runs the tests against PostgreSQL on every push. English summary below.*

![CI](https://github.com/Ahmetrahatlik/stok-api/actions/workflows/ci.yml/badge.svg)

## Neden?

Bir hırdavat dükkânı için internetsiz çalışan bir masaüstü stok programı geliştirdim. Bu proje aynı iş kurallarını sunucu tarafında, çok kullanıcılı bir API olarak yeniden kuruyor.

## Özellikler

- **Ürünler:** ekleme, güncelleme, arama, kritik stok listesi
- **Stok hareketleri:** mal girişi (alış fiyatı güncellenir), sayım düzeltmesi, hareket geçmişi
- **Satış:** birden çok kalem, nakit veya veresiye; stok yetmezse satışın tamamı iptal olur
- **Veresiye:** müşteri borcu, tahsilat, borçlu müşteriler listesi
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
uvicorn app.main:app --reload
```

## Testler

```bash
pytest -q
```

Yerelde testler bellekte çalışan SQLite kullanır. CI'da `DATABASE_URL` PostgreSQL'i gösterir, aynı testler gerçek veritabanında çalışır.

## Örnek istekler

```bash
# Ürün ekle
curl -X POST localhost:8000/products -H "Content-Type: application/json" \
  -d '{"name": "Çekiç", "purchase_price": "80", "sale_price": "120", "min_stock": "5"}'

# 10 adet mal girişi
curl -X POST localhost:8000/stock/purchases -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": "10"}'

# Müşteri ekle ve veresiye satış yap
curl -X POST localhost:8000/customers -H "Content-Type: application/json" -d '{"name": "Mehmet Usta"}'
curl -X POST localhost:8000/sales -H "Content-Type: application/json" \
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
