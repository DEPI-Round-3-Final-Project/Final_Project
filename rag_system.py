import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import re
import pickle
import os
from pathlib import Path


class RAGSystem:
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2", cache_dir="rag_cache"):
        """
        Professional RAG system using Sentence Transformers with caching

        Model used: paraphrase-multilingual-mpnet-base-v2
        - Supports 50+ languages including Arabic
        - Much better than regular Arabic BERT
        - Specialized in semantic search

        🆕 Enhancements:
        - Save embeddings to disk
        - Load cache instead of re-processing
        - Saves time on every run
        """
        print("\n" + "="*70)
        print("🔧 تحميل نموذج RAG...")
        print(f"📦 الموديل: {model_name}")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Cache file paths
        self.index_path = self.cache_dir / "faiss_index.bin"
        self.texts_path = self.cache_dir / "texts.pkl"
        self.metadata_path = self.cache_dir / "metadata.pkl"
        self.embeddings_cache_path = self.cache_dir / "embeddings_cache.pkl"

        try:
            self.model = SentenceTransformer(model_name)
            print("✅ تم تحميل الموديل بنجاح!")
        except Exception as e:
            print(f"⚠️ فشل تحميل الموديل الأساسي، استخدام بديل...")
            self.model = SentenceTransformer(
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            print("✅ تم تحميل الموديل البديل")

        print("="*70 + "\n")

        self.index = None
        self.texts = []
        self.metadata = []
        self.embeddings_cache = {}

        # 🆕 Attempt to load existing cache
        self._load_cache()

    def _load_cache(self):
        """🆕 Load the saved cache"""
        if self.index_path.exists() and self.texts_path.exists() and self.metadata_path.exists():
            try:
                print("\n" + "="*70)
                print("📂 وجدت cache محفوظ، جاري التحميل...")

                # Load index
                self.index = faiss.read_index(str(self.index_path))

                # Load texts
                with open(self.texts_path, 'rb') as f:
                    self.texts = pickle.load(f)

                # Load metadata
                with open(self.metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)

                # Load embeddings cache
                if self.embeddings_cache_path.exists():
                    with open(self.embeddings_cache_path, 'rb') as f:
                        self.embeddings_cache = pickle.load(f)

                print(f"✅ تم تحميل الـ cache بنجاح!")
                print(f"📊 عدد النصوص: {len(self.texts)}")
                print(f"💾 عدد embeddings محفوظة: {len(self.embeddings_cache)}")
                print("="*70 + "\n")

                return True
            except Exception as e:
                print(f"⚠️ فشل تحميل الـ cache: {e}")
                print("سيتم إعادة بناء الفهرس...")
                return False

        return False

    def _save_cache(self):
        """🆕 Save cache to disk"""
        try:
            print("\n💾 جاري حفظ الـ cache...")

            # Save index
            if self.index is not None:
                faiss.write_index(self.index, str(self.index_path))

            # Save texts
            with open(self.texts_path, 'wb') as f:
                pickle.dump(self.texts, f)

            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)

            # Save embeddings cache
            with open(self.embeddings_cache_path, 'wb') as f:
                pickle.dump(self.embeddings_cache, f)

            print("✅ تم حفظ الـ cache بنجاح!")
            print(f"📁 الموقع: {self.cache_dir}")

        except Exception as e:
            print(f"⚠️ فشل حفظ الـ cache: {e}")

    def _preprocess_for_embedding(self, text):
        """Pre-process text before embedding"""
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text[:512]
        return text.strip()

    def embed_text(self, text):
        """Convert text to embedding"""
        text_hash = hash(text)
        if text_hash in self.embeddings_cache:
            return self.embeddings_cache[text_hash]

        processed_text = self._preprocess_for_embedding(text)
        embedding = self.model.encode(processed_text, convert_to_numpy=True)
        self.embeddings_cache[text_hash] = embedding

        return embedding

    def build_index(self, texts, metadata):
        """🔧 Build search index - enhanced with Cache saving"""

        # 🆕 Check for updated cache
        if self.index is not None and len(self.texts) == len(texts):
            print("\n✅ الفهرس موجود بالفعل، لا حاجة لإعادة البناء!")
            return

        print("\n" + "="*70)
        print("🔨 بناء فهرس RAG...")
        print(f"📊 عدد النصوص: {len(texts)}")

        self.texts = texts
        self.metadata = metadata

        print("⚙️  توليد embeddings...")
        embeddings = []

        for i, text in enumerate(texts):
            if (i + 1) % 50 == 0:
                print(f"   معالجة: {i + 1}/{len(texts)}")

            embedding = self.embed_text(text)
            embeddings.append(embedding)

        embeddings = np.array(embeddings).astype('float32')

        print("🔍 بناء فهرس البحث...")
        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        print(f"✅ تم بناء الفهرس! ({dimension} أبعاد)")
        print("="*70 + "\n")

        # 🆕 Save cache
        self._save_cache()

    def search(self, query, k=5, min_score=0.4, subject_filter=None):
        """
        Search for the closest texts to the query - enhanced

        Enhancements:
        - Add subject filtering
        - Increase min_score from 0.35 to 0.4 (more strict)
        - Add better result filtering
        - Assess result quality
        """
        if self.index is None or len(self.texts) == 0:
            print("⚠️ الفهرس فارغ!")
            return []

        query_embedding = self.embed_text(
            query).reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)

        # Search for more results for filtering
        scores, indices = self.index.search(
            query_embedding, min(k * 5, len(self.texts)))  # increase count for filtering

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.texts) and score >= min_score:
                # 🔧 Strict subject filtering
                if subject_filter:
                    if self.metadata[idx]["subject"] != subject_filter:
                        continue  # Skip results from other subjects entirely

                results.append({
                    "text": self.texts[idx],
                    "metadata": self.metadata[idx],
                    "score": float(score),
                    "relevance": self._get_relevance_label(score),
                    "quality": self._assess_result_quality(self.texts[idx], query)
                })

        # Sort by quality and score
        results = sorted(
            results,
            key=lambda x: (x["quality"]["overall_score"], x["score"]),
            reverse=True
        )

        return results[:k]

    def _assess_result_quality(self, text, query):
        """
        🆕 Assess result quality

        Checks:
        1. Presence of keywords from the query in the text
        2. Text length (not too short)
        3. Content diversity
        """
        quality = {
            "keyword_match": 0,
            "length_score": 0,
            "diversity_score": 0,
            "overall_score": 0
        }

        # 1. Check keywords
        query_words = set(self._extract_keywords(query))
        text_words = set(self._extract_keywords(text))

        if query_words:
            matched = query_words.intersection(text_words)
            quality["keyword_match"] = len(matched) / len(query_words)

        # 2. Check length
        if 100 <= len(text) <= 1000:
            quality["length_score"] = 1.0
        elif len(text) < 100:
            quality["length_score"] = len(text) / 100
        else:
            quality["length_score"] = 0.8

        # 3. Check diversity
        unique_words = len(set(text.split()))
        total_words = len(text.split())
        if total_words > 0:
            quality["diversity_score"] = min(unique_words / total_words, 1.0)

        # Overall score
        quality["overall_score"] = (
            quality["keyword_match"] * 0.5 +
            quality["length_score"] * 0.3 +
            quality["diversity_score"] * 0.2
        )

        return quality

    def search_with_quality_filter(self, query, k=5, min_quality=0.3, subject_filter=None):
        """
        🆕 Search with quality filtering

        Args:
            query: Search text
            k: Desired number of results
            min_quality: Minimum quality threshold
            subject_filter: Filter by subject
        """
        return self.search(query, k=k, min_score=min_quality, subject_filter=subject_filter)

    def search_with_keywords(self, query, k=5, subject_filter=None):
        """Search with keywords as fallback - enhanced"""
        # First: regular search with quality filtering
        results = self.search_with_quality_filter(
            query, k=k, min_quality=0.3, subject_filter=subject_filter)

        # If we don't find enough results, search by keywords
        if len(results) < 2:
            keywords = self._extract_keywords(query)

            for keyword in keywords[:3]:  # Only the first 3 words
                if len(keyword) > 3:
                    more_results = self.search(
                        keyword, k=3, min_score=0.3, subject_filter=subject_filter)
                    results.extend(more_results)

        # Remove duplicates
        seen_texts = set()
        unique_results = []
        for result in results:
            text_hash = hash(result["text"])
            if text_hash not in seen_texts:
                seen_texts.add(text_hash)
                unique_results.append(result)

        return unique_results[:k]

    def _extract_keywords(self, text):
        """Extract keywords from text"""
        text = re.sub(r'[إأآا]', 'ا', text)
        text = re.sub(r'[ىي]', 'ي', text)

        words = re.findall(r'[\u0600-\u06FF]+', text)
        keywords = [w for w in words if len(w) > 3]

        return keywords

    def _get_relevance_label(self, score):
        """Classify similarity score"""
        if score >= 0.7:
            return "عالي جداً"
        elif score >= 0.5:
            return "عالي"
        elif score >= 0.35:
            return "متوسط"
        else:
            return "ضعيف"

    def add_texts(self, new_texts, new_metadata):
        """Add new texts"""
        print(f"➕ إضافة {len(new_texts)} نص جديد...")

        new_embeddings = []
        for text in new_texts:
            embedding = self.embed_text(text)
            new_embeddings.append(embedding)

        new_embeddings = np.array(new_embeddings).astype('float32')
        faiss.normalize_L2(new_embeddings)

        self.index.add(new_embeddings)
        self.texts.extend(new_texts)
        self.metadata.extend(new_metadata)

        print(f"✅ تمت الإضافة! إجمالي النصوص: {len(self.texts)}")

        # 🆕 Save updated cache
        self._save_cache()

    def clear_cache(self):
        """🆕 Delete the saved cache"""
        try:
            if self.index_path.exists():
                os.remove(self.index_path)
            if self.texts_path.exists():
                os.remove(self.texts_path)
            if self.metadata_path.exists():
                os.remove(self.metadata_path)
            if self.embeddings_cache_path.exists():
                os.remove(self.embeddings_cache_path)

            print("✅ تم حذف الـ cache بنجاح!")
        except Exception as e:
            print(f"⚠️ فشل حذف الـ cache: {e}")

    def get_stats(self):
        """System statistics"""
        return {
            "total_texts": len(self.texts),
            "index_size": self.index.ntotal if self.index else 0,
            "cache_size": len(self.embeddings_cache),
            "cache_exists": self.index_path.exists()
        }
    