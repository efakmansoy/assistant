"""
RAG (Retrieval-Augmented Generation) Sistemi
PDF işleme, vektör veritabanı ve LLM entegrasyonu
"""
import os
import logging
from typing import List, Optional
from pathlib import Path

# PDF işleme için
import fitz  # PyMuPDF
from unstructured.partition.pdf import partition_pdf

# LLaMA Index için
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

# Chroma için
import chromadb
from chromadb.config import Settings as ChromaSettings

# Gemini API için
import google.generativeai as genai

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    """RAG sistemi ana sınıfı"""
    
    def __init__(self, data_dir: str = "data", chroma_db_dir: str = "data/chroma_db"):
        self.data_dir = Path(data_dir)
        self.chroma_db_dir = Path(chroma_db_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.chroma_db_dir.mkdir(parents=True, exist_ok=True)
        
        # Embedding model ayarları
        Settings.embed_model = HuggingFaceEmbedding(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Chroma client'ı başlat
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.chroma_db_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Koleksiyon oluştur/al
        self.collection = self.chroma_client.get_or_create_collection(
            name="project_documents"
        )
        
        # Vector store ve index
        self.vector_store = ChromaVectorStore(chroma_collection=self.collection)
        self.index = None
        
        # Gemini API ayarları
        self.setup_gemini()
        
        logger.info("RAG sistemi başlatıldı")
    
    def setup_gemini(self):
        """Gemini API ayarlarını yap"""
        # Çevre değişkeninden API key'i al
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
            logger.info("Gemini API yapılandırıldı")
        else:
            self.gemini_model = None
            logger.warning("GEMINI_API_KEY çevre değişkeni bulunamadı")
    
    def process_pdf_document(self, file_path: str, chunk_size: int = 1000) -> List[Document]:
        """
        PDF dökümanını işle ve LlamaIndex Document'larına dönüştür
        Büyük dosyalar için sayfa aralıkları ile çalışır
        """
        documents = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Dosya bulunamadı: {file_path}")
            return documents
        
        try:
            # PyMuPDF ile sayfa sayısını kontrol et
            doc = fitz.open(file_path)
            total_pages = len(doc)
            doc.close()
            
            logger.info(f"PDF işleniyor: {file_path.name}, Toplam sayfa: {total_pages}")
            
            # Büyük dosyalar için batch işleme (örnek: 20 sayfa grupları)
            batch_size = 20
            
            for start_page in range(0, total_pages, batch_size):
                end_page = min(start_page + batch_size, total_pages)
                
                logger.info(f"Sayfa {start_page+1}-{end_page} işleniyor...")
                
                # Unstructured ile PDF'i işle
                elements = partition_pdf(
                    filename=str(file_path),
                    strategy="hi_res",  # Yüksek çözünürlük için
                    infer_table_structure=True,  # Tablo yapısını algıla
                    extract_images_in_pdf=False,  # Şimdilik resim çıkarma
                    pages=[i for i in range(start_page, end_page)]
                )
                
                # Elementleri metne dönüştür
                batch_text = ""
                for element in elements:
                    if hasattr(element, 'text'):
                        batch_text += element.text + "\n"
                
                # Document oluştur
                if batch_text.strip():
                    doc_metadata = {
                        "source": str(file_path),
                        "filename": file_path.name,
                        "page_range": f"{start_page+1}-{end_page}",
                        "total_pages": total_pages
                    }
                    
                    # Metni chunk'lara böl
                    chunks = self._split_text(batch_text, chunk_size)
                    
                    for i, chunk in enumerate(chunks):
                        chunk_metadata = doc_metadata.copy()
                        chunk_metadata["chunk_id"] = f"{start_page+1}-{end_page}_{i}"
                        
                        documents.append(Document(
                            text=chunk,
                            metadata=chunk_metadata
                        ))
            
            logger.info(f"PDF işleme tamamlandı. {len(documents)} döküman oluşturuldu.")
            
        except Exception as e:
            logger.error(f"PDF işleme hatası: {e}")
            
            # Fallback: PyMuPDF ile basit metin çıkarma
            try:
                doc = fitz.open(file_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                
                if text.strip():
                    chunks = self._split_text(text, chunk_size)
                    for i, chunk in enumerate(chunks):
                        documents.append(Document(
                            text=chunk,
                            metadata={
                                "source": str(file_path),
                                "filename": file_path.name,
                                "chunk_id": f"fallback_{i}",
                                "extraction_method": "pymupdf_fallback"
                            }
                        ))
                    
                    logger.info(f"Fallback ile {len(documents)} döküman oluşturuldu.")
                
            except Exception as fallback_error:
                logger.error(f"Fallback PDF işleme hatası: {fallback_error}")
        
        return documents
    
    def _split_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Metni belirtilen boyutta parçalara böl"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Kelime sınırında kes
            if end < len(text):
                # Son kelimeyi tamamla
                while end < len(text) and text[end] != ' ':
                    end += 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start <= 0:
                start = end
        
        return chunks
    
    def add_documents_to_index(self, documents: List[Document]):
        """Dökümanları vektör indeksine ekle"""
        if not documents:
            logger.warning("Eklenecek döküman bulunamadı")
            return
        
        try:
            if self.index is None:
                self.index = VectorStoreIndex.from_documents(
                    documents,
                    vector_store=self.vector_store
                )
            else:
                # Mevcut indekse döküman ekle
                for doc in documents:
                    self.index.insert(doc)
            
            logger.info(f"{len(documents)} döküman indekse eklendi")
            
        except Exception as e:
            logger.error(f"İndeksleme hatası: {e}")
    
    def search_documents(self, query: str, top_k: int = 5) -> List[str]:
        """Dökümanları ara ve ilgili parçaları döndür"""
        if self.index is None:
            logger.warning("İndeks bulunamadı")
            return []
        
        try:
            query_engine = self.index.as_query_engine(similarity_top_k=top_k)
            response = query_engine.query(query)
            
            # Kaynak dökümanları al
            contexts = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    contexts.append(node.text)
            
            return contexts
            
        except Exception as e:
            logger.error(f"Arama hatası: {e}")
            return []
    
    def generate_response(self, query: str, user_role: str = "student", project_context: str = "", top_k: int = 3) -> str:
        """
        Gemini API ile yanıt oluştur
        RAG context'i ile birleştirilen prompt kullanır
        """
        if not self.gemini_model:
            return "Gemini API yapılandırılmamış. Lütfen GEMINI_API_KEY çevre değişkenini ayarlayın."
        
        try:
            # İlgili dökümanları ara
            contexts = self.search_documents(query, top_k)
            
            # Rol tabanlı prompt oluştur
            role_prompts = {
                "student": "Sen öğrencilere proje geliştirme konusunda yardımcı olan bir AI asistansın. Açıklayıcı, destekleyici ve öğretici bir dil kullan.",
                "advisor": "Sen danışmanlara proje yönetimi ve öğrenci rehberliği konusunda yardımcı olan bir AI asistansın. Profesyonel ve analitik bir yaklaşım benimse.",
                "admin": "Sen sistem yöneticilerine platform yönetimi konusunda yardımcı olan bir AI asistansın."
            }
            
            role_prompt = role_prompts.get(user_role, role_prompts["student"])
            
            # Context'i birleştir
            context_text = "\n\n".join(contexts) if contexts else "İlgili döküman bulunamadı."
            
            # Ana prompt'u oluştur
            prompt = f"""
{role_prompt}

Proje Bağlamı: {project_context}

İlgili Döküman İçeriği:
{context_text}

Kullanıcı Sorusu: {query}

Lütfen yukarıdaki bağlam ve döküman içeriğini kullanarak kullanıcının sorusunu yanıtla. Eğer döküman içeriği soruyla ilgili değilse, genel bilgilerinle yardım et.
"""
            
            # Gemini'den yanıt al
            response = self.gemini_model.generate_content(prompt)
            
            if response.text:
                return response.text
            else:
                return "Yanıt oluşturulamadı. Lütfen sorunuzu tekrar ifade edin."
                
        except Exception as e:
            logger.error(f"Yanıt oluşturma hatası: {e}")
            return f"Bir hata oluştu: {str(e)}"
    
    def get_ai_response(self, question: str, user_role: str = "student", project_context: str = "") -> str:
        """
        Kullanıcı sorusuna AI yanıtı üret
        RAG sistemi ile döküman bilgilerini kullanarak yanıt oluştur
        """
        try:
            # Rol bazlı prompt oluştur
            role_prompts = {
                "student": "Sen bir öğrenci proje geliştirme asistanısın. Öğrencilere proje geliştirme sürecinde rehberlik et.",
                "advisor": "Sen bir danışman asistanısın. Danışmanlara öğrenci projelerini değerlendirme ve yönlendirme konusunda yardım et.",
                "admin": "Sen bir sistem yöneticisi asistanısın. Genel proje istatistikleri ve sistem yönetimi konularında destek sağla."
            }
            
            system_prompt = role_prompts.get(user_role, role_prompts["student"])
            
            # RAG ile ilgili dokümanları ara
            relevant_context = ""
            if self.index:
                try:
                    query_engine = self.index.as_query_engine(similarity_top_k=3)
                    rag_response = query_engine.query(question)
                    if rag_response.response:
                        relevant_context = f"\n\nİlgili döküman bilgileri:\n{rag_response.response}"
                except Exception as e:
                    logger.warning(f"RAG sorgu hatası: {e}")
            
            # Final prompt'u oluştur
            final_prompt = f"""
{system_prompt}

Proje Bağlamı: {project_context}

Kullanıcı Sorusu: {question}
{relevant_context}

Lütfen yardımcı ve bilgilendirici bir yanıt ver. Türkçe yanıt ver.
"""

            if self.gemini_model:
                response = self.gemini_model.generate_content(final_prompt)
                if response.text:
                    return response.text
                else:
                    return "Yanıt oluşturulamadı. Lütfen sorunuzu tekrar ifade edin."
            else:
                return "AI sistemi şu anda kullanılamıyor. Lütfen daha sonra tekrar deneyin."
                
        except Exception as e:
            logger.error(f"AI yanıt oluşturma hatası: {e}")
            return "Üzgünüm, şu anda bir teknik sorun yaşıyorum. Lütfen daha sonra tekrar deneyin."
    
    def add_document(self, file_path: str, project_id: int = None):
        """
        Yeni döküman ekle ve indeksle
        """
        try:
            documents = self.process_pdf_document(file_path)
            if documents:
                # Proje ID'sini metadata olarak ekle
                for doc in documents:
                    if project_id:
                        doc.metadata["project_id"] = str(project_id)
                
                self.add_documents_to_index(documents)
                logger.info(f"Döküman başarıyla eklendi: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Döküman ekleme hatası: {e}")
            return False
    
    def process_and_index_file(self, file_path: str):
        """Dosyayı işle ve indeksle (ana fonksiyon)"""
        documents = self.process_pdf_document(file_path)
        if documents:
            self.add_documents_to_index(documents)
            return True
        return False

# Global RAG sistemi instance'ı
rag_system = None

def init_rag_system():
    """RAG sistemini başlat"""
    global rag_system
    try:
        rag_system = RAGSystem()
        logger.info("RAG sistemi başarıyla başlatıldı")
        return rag_system
    except Exception as e:
        logger.error(f"RAG sistemi başlatma hatası: {e}")
        return None

def get_rag_system():
    """RAG sistemi instance'ını al"""
    global rag_system
    if rag_system is None:
        rag_system = init_rag_system()
    return rag_system