import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import re
import unicodedata

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class PDFExtractor:
    def __init__(self):
        self.arabic_reshaper = None
        try:
            import arabic_reshaper
            from bidi.algorithm import get_display
            self.arabic_reshaper = arabic_reshaper
            self.get_display = get_display
        except:
            print("⚠️ تحذير: arabic_reshaper غير متوفر") # Warning: arabic_reshaper is not available

    def process_pdf_page_by_page(self, pdf_path):
        """Professional text extraction from PDF"""
        print(f"\n{'='*70}")
        print(f"📖 معالجة: {pdf_path}") # Processing: {pdf_path}
        print(f"{'='*70}\n")

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            print(f"📄 عدد الصفحات: {total_pages}\n") # Number of pages: {total_pages}

            successful_pages = 0

            for page_num in range(total_pages):
                page = doc[page_num]

                # Extract text
                raw_text = page.get_text("text")

                # Deep cleaning
                cleaned_text = self._deep_clean(raw_text)

                # If the text is short, try OCR
                if len(cleaned_text) < 100:
                    ocr_text = self._extract_with_ocr(page)
                    if ocr_text:
                        cleaned_text = self._deep_clean(ocr_text)

                # Check quality
                if self._is_quality_text(cleaned_text):
                    successful_pages += 1
                    print(f"✅ صفحة {page_num + 1}: {len(cleaned_text)} حرف") # Page {page_num + 1}: {len(cleaned_text)} characters

                    # Show preview
                    preview = self._get_preview(cleaned_text, 80)
                    print(f"   📝 {preview}\n")

                    yield cleaned_text, page_num + 1
                else:
                    print(
                        f"⏭️  صفحة {page_num + 1}: تم تخطيها (جودة منخفضة)\n") # Page {page_num + 1}: Skipped (low quality)

            doc.close()

            print(f"{'='*70}")
            print(f"✅ نجح استخراج {successful_pages}/{total_pages} صفحة") # Successfully extracted {successful_pages}/{total_pages} pages
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"❌ خطأ: {e}\n") # Error: {e}

    def _deep_clean(self, text):
        """Deep and advanced cleaning for Arabic text"""
        if not text:
            return ""

        # 1. Normalize Unicode (handle composite characters)
        text = unicodedata.normalize('NFKC', text)

        # 2. Remove diacritics and elongation (kashida)
        text = re.sub(r'[\u064B-\u0652\u0640]', '', text)

        # 3. Normalize hamzas
        text = re.sub(r'[إأآا]', 'ا', text)
        text = re.sub(r'[ىي]', 'ي', text)
        text = re.sub(r'ة', 'ه', text)

        # 4. Remove harmful special characters (but keep useful punctuation)
        text = re.sub(
            r'[^\u0600-\u06FF\u0750-\u077F'  # Arabic
            r'a-zA-Z0-9'  # English and numbers
            r'\s\.\,\:\?\!\-\(\)\[\]'  # Useful punctuation
            r'\n]',  # New line
            ' ',
            text
        )

        # 5. Remove symbols and icons
        text = re.sub(r'[\u2000-\u2BFF\u2E00-\u2E7F]', '', text)

        # 6. Clean up spaces
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # 7. Remove solitary numbers (page numbers)
        text = re.sub(r'\n\d+\s*\n', '\n', text)
        text = re.sub(r'^\d+\s*', '', text, flags=re.MULTILINE)

        # 8. Clean up lines
        lines = text.split('\n')
        clean_lines = []

        for line in lines:
            line = line.strip()

            # Skip very short lines
            if len(line) < 10:
                continue

            # Skip lines full of symbols
            non_text = len(re.findall(r'[^\u0600-\u06FFa-zA-Z0-9\s]', line))
            if non_text / max(len(line), 1) > 0.4:
                continue

            # Skip duplicate lines
            if clean_lines and line == clean_lines[-1]:
                continue

            clean_lines.append(line)

        # 9. Reconstruct the text
        text = '\n'.join(clean_lines)

        # 10. Final cleaning
        text = text.strip()

        return text

    def _extract_with_ocr(self, page):
        """Enhanced OCR"""
        try:
            # Convert to high-resolution image
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Image processing
            img = img.convert('L')
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(2.5)
            img = img.filter(ImageFilter.SHARPEN)

            # OCR
            custom_config = r'--oem 3 --psm 6 -l ara'
            text = pytesseract.image_to_string(img, config=custom_config)

            return text

        except Exception as e:
            return ""

    def _is_quality_text(self, text):
        """Text quality check"""
        if not text or len(text) < 50:
            return False

        # Calculate Arabic character ratio
        arabic = len(re.findall(r'[\u0600-\u06FF]', text))
        total = len(re.sub(r'\s', '', text))

        if total == 0:
            return False

        arabic_ratio = arabic / total

        # Must be at least 25% Arabic
        if arabic_ratio < 0.25:
            return False

        # Calculate word count
        words = text.split()
        if len(words) < 10:
            return False

        return True

    def _get_preview(self, text, length=80):
        """Show a text preview"""
        text = text.replace('\n', ' ')
        if len(text) > length:
            return text[:length] + "..."
        return text
    