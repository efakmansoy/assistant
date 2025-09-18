# RAG Assistant - AI Destekli Proje Geliştirme Platformu

Bu proje, öğrenci ve danışmanlara proje geliştirme sürecinde yardımcı olacak bir AI destekli platform oluşturmayı amaçlamaktadır.

## 🚀 Özellikler

### 🤖 AI Asistan
- **Google Gemini API** entegrasyonu
- **LLaMA Index** ile PDF döküman analizi
- **Chroma** vektör veritabanı ile akıllı arama
- Rol tabanlı prompt'lar (öğrenci/danışman/admin)
- Gerçek zamanlı chat sistemi

### 👥 Kullanıcı Yönetimi
- **Üç rol tipi**: Öğrenci, Danışman, Admin
- Güvenli kimlik doğrulama sistemi
- Rol tabanlı erişim kontrolü
- Kullanıcı profil yönetimi

### 📋 Proje Yönetimi
- Proje oluşturma ve takibi
- Danışman atama sistemi
- İlerleme izleme
- Yarışma entegrasyonu
- Döküman yükleme ve analizi

### 🏆 Yarışma Sistemi
- Yarışma oluşturma ve yönetimi
- Proje-yarışma eşleştirme
- Son teslim tarihi takibi
- Gereksinim yönetimi

## 🛠️ Teknoloji Stack'i

### Backend
- **Python Flask** - Web framework
- **Flask-SQLAlchemy** - ORM
- **Flask-Login** - Kimlik doğrulama
- **Flask-SocketIO** - Gerçek zamanlı iletişim
- **SQLite** - Ana veritabanı

### AI & RAG
- **LLaMA Index** - Döküman işleme ve indeksleme
- **Google Gemini API** - Large Language Model
- **Chroma** - Vektör veritabanı
- **unstructured[pdf]** - PDF parsing
- **PyMuPDF** - PDF işleme (fallback)

### Frontend
- **HTML5 & CSS3**
- **Bootstrap 5** - UI framework
- **JavaScript (ES6+)** - Dinamik içerik
- **Socket.IO Client** - Gerçek zamanlı chat
- **Font Awesome** - İkonlar

## 📦 Kurulum

### 1. Repo'yu klonlayın
```bash
git clone <repository-url>
cd rag-assistant
```

### 2. Sanal ortam oluşturun
```bash
python -m venv venv
```

### 3. Sanal ortamı aktifleştirin
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 4. Bağımlılıkları yükleyin
```bash
pip install -r requirements.txt
```

### 5. Çevre değişkenlerini ayarlayın
```bash
# .env.example dosyasını kopyalayın
cp .env.example .env

# .env dosyasını editleyip gerekli değişkenleri ayarlayın
# Özellikle GEMINI_API_KEY'i eklemeyi unutmayın
```

### 6. Veritabanını başlatın
```bash
python app.py
```
İlk çalıştırmada otomatik olarak:
- SQLite veritabanı oluşturulur
- Admin kullanıcısı oluşturulur (admin/admin123)
- RAG sistemi başlatılır

## 🔧 Konfigürasyon

### Google Gemini API
1. [Google AI Studio](https://makersuite.google.com/app/apikey)'ya gidin
2. API key oluşturun
3. `.env` dosyasına `GEMINI_API_KEY=your-api-key` ekleyin

### Dosya Yükleme
- Maksimum dosya boyutu: 16MB
- Desteklenen formatlar: PDF
- Yükleme klasörü: `uploads/`

## 📁 Proje Yapısı

```
rag-assistant/
├── app.py                 # Ana Flask uygulaması
├── models.py             # Veritabanı modelleri
├── routes.py             # URL route'ları
├── chat_handlers.py      # Socket.IO chat handler'ları
├── rag_system.py         # RAG sistemi ana modülü
├── requirements.txt      # Python bağımlılıkları
├── .env.example         # Çevre değişkenleri örneği
├── templates/           # HTML şablonları
│   ├── base.html
│   ├── index.html
│   ├── chat.html
│   └── auth/
├── static/              # Statik dosyalar
│   ├── css/
│   └── js/
├── data/               # Veri dosyaları
│   └── chroma_db/      # Vektör veritabanı
└── uploads/            # Yüklenen dosyalar
```

## 🎯 Kullanım

### 1. Uygulamayı başlatın
```bash
python app.py
```
Uygulama `http://localhost:5000` adresinde çalışacak.

### 2. İlk giriş
- Admin: `admin` / `admin123`
- Yeni kullanıcı kaydı yapabilirsiniz

### 3. Proje oluşturma
1. Dashboard'a gidin
2. "Yeni Proje" butonuna tıklayın
3. Proje bilgilerini doldurun
4. PDF dökümanlarınızı yükleyin

### 4. AI Asistan kullanımı
1. "AI Asistan" sekmesine gidin
2. Proje seçin (isteğe bağlı)
3. Sorularınızı yazın
4. AI'dan akıllı yanıtlar alın

## 🔧 Geliştirme

### Debug Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
python app.py
```

### Veritabanı Reset
```bash
# Veritabanı dosyasını silin
rm rag_assistant.db

# Uygulamayı yeniden başlatın
python app.py
```

### Yeni Özellik Ekleme
1. Model değişiklikleri için `models.py`
2. API endpoint'leri için `routes.py`
3. Frontend için `templates/` ve `static/`
4. RAG işlevleri için `rag_system.py`

## 📝 API Dokümantasyonu

### Kimlik Doğrulama
- `POST /auth/login` - Kullanıcı girişi
- `POST /auth/register` - Kullanıcı kaydı
- `GET /auth/logout` - Çıkış

### Projeler
- `GET /api/projects` - Proje listesi
- `POST /api/projects` - Yeni proje oluştur
- `GET /api/projects/<id>` - Proje detayı

### Yarışmalar
- `GET /api/competitions` - Yarışma listesi
- `POST /admin/competitions/add` - Yarışma ekle (Admin)

### Chat
- Socket.IO event'leri:
  - `send_message` - Mesaj gönder
  - `receive_message` - Mesaj al
  - `join_chat` - Sohbete katıl

## 🚀 Deployment

### Production Ayarları
```bash
# .env dosyasında
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=very-secure-random-key
```

### Docker (İsteğe bağlı)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun: `git checkout -b feature/amazing-feature`
3. Commit'leyin: `git commit -m 'Add amazing feature'`
4. Push yapın: `git push origin feature/amazing-feature`
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🆘 Sorun Giderme

### Yaygın Sorunlar

1. **Gemini API Hatası**
   - API key'in doğru ayarlandığından emin olun
   - API kotanızı kontrol edin

2. **PDF İşleme Hatası**
   - Dosya boyutunu kontrol edin (max 16MB)
   - PDF'in bozuk olmadığından emin olun

3. **Chat Bağlantı Sorunu**
   - Socket.IO portlarının açık olduğundan emin olun
   - Firewall ayarlarını kontrol edin

### Loglar
```bash
# Flask loglarını görüntüle
tail -f logs/app.log

# Konsol çıktısını takip et
python app.py
```

## 📧 İletişim

Sorularınız için issue açabilir veya doğrudan iletişime geçebilirsiniz.

---

**RAG Assistant** - AI ile güçlendirilmiş proje geliştirme deneyimi! 🚀