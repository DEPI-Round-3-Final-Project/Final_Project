import os
from config import TELEGRAM_TOKEN, PDF_DIRECTORY, EXTRACTED_TEXT_DIRECTORY
from data_extractor import PDFExtractor
from text_preprocessor import TextPreprocessor
from database_manager import DatabaseManager
from telegram_bot import StudyAssistantBot
from reminder_system import ReminderSystem


def setup_directories():
    """Create directories"""
    os.makedirs(PDF_DIRECTORY, exist_ok=True)
    os.makedirs(EXTRACTED_TEXT_DIRECTORY, exist_ok=True)
    os.makedirs("rag_cache", exist_ok=True)  # 🆕 cache folder
    print("✅ تم إنشاء المجلدات\n")


def process_single_pdf(pdf_name, subject_name):
    """Process only one book (Biology or Arabic)"""
    pdf_path = os.path.join(PDF_DIRECTORY, pdf_name)

    if not os.path.exists(pdf_path):
        print(f"❌ تحذير: ملف {pdf_name} غير موجود!\n")
        return

    print("\n" + "="*70)
    print(f"📚 بدء معالجة كتاب: {subject_name}")
    print("="*70 + "\n")

    preprocessor = TextPreprocessor()
    db_manager = DatabaseManager()
    extractor = PDFExtractor()

    processed_chunks = 0
    total_characters = 0

    for page_text, page_num in extractor.process_pdf_page_by_page(pdf_path):

        # Clean the text
        processed_text = preprocessor.preprocess_text(page_text)

        if not preprocessor.is_meaningful_text(processed_text):
            continue

        # Split the text into chunks
        for chunk in preprocessor.chunk_text(processed_text, chunk_size=800, overlap=100):

            if len(chunk) > 100:  # Ignore very short texts

                # Divide the chapter based on every 20 pages
                chapter_num = (page_num - 1) // 20 + 1

                db_manager.add_textbook_content(
                    subject=subject_name,
                    grade_level="secondary",
                    chapter=f"Chapter {chapter_num}",
                    content=chunk,
                    page_number=page_num,
                    content_type="text"
                )

                processed_chunks += 1
                total_characters += len(chunk)

    print("\n" + "="*70)
    print(f"✅ اكتملت معالجة كتاب: {subject_name}")
    print(f"📊 الإحصائيات:")
    print(f"   • عدد القطع: {processed_chunks}")
    print(f"   • إجمالي الأحرف: {total_characters:,}")
    print(
        f"   • متوسط طول القطعة: {total_characters // max(processed_chunks, 1)} حرف")
    print("="*70 + "\n")


def process_pdfs():
    """Process all PDF files (Biology + Arabic)"""
    # Process Biology
    process_single_pdf("biology.pdf", "biology")

    # Process Arabic
    process_single_pdf("arabic.pdf", "arabic")


def verify_database():
    """Verify the database"""
    print("\n" + "="*70)
    print("🔍 التحقق من قاعدة البيانات...")
    print("="*70 + "\n")

    db_manager = DatabaseManager()

    for subject in ["biology", "arabic"]:
        content = db_manager.get_textbook_content(subject)

        if content:
            print(f"✅ محتوى {subject}: {len(content)} قطعة")

            # Show sample
            sample = content[0]
            print(f"\n📝 عينة من المحتوى ({subject}):")
            print(f"   الفصل: {sample[0]}")
            print(f"   الصفحة: {sample[2]}")
            preview = sample[1][:150].replace('\n', ' ')
            print(f"   النص: {preview}...\n")
        else:
            print(f"⚠️ لا يوجد محتوى في قاعدة البيانات لمادة {subject}!\n")

    print("="*70 + "\n")


def check_cache_status():
    """🆕 Check cache status"""
    cache_files = [
        "rag_cache/faiss_index.bin",
        "rag_cache/texts.pkl",
        "rag_cache/metadata.pkl",
        "rag_cache/embeddings_cache.pkl"
    ]

    all_exist = all(os.path.exists(f) for f in cache_files)

    if all_exist:
        print("\n" + "="*70)
        print("💾 حالة الـ Cache:")
        print("="*70)
        print("✅ وجدت ملفات cache محفوظة!")
        print("⚡ سيتم تحميل الفهرس مباشرة (بدون إعادة معالجة)")

        # Show file sizes
        for f in cache_files:
            size = os.path.getsize(f) / (1024 * 1024)  # MB
            print(f"   📁 {os.path.basename(f)}: {size:.2f} MB")

        print("="*70 + "\n")
        return True
    else:
        print("\n" + "="*70)
        print("📝 حالة الـ Cache:")
        print("="*70)
        print("⚠️ لم يتم العثور على cache محفوظ")
        print("⏳ سيتم بناء الفهرس (سيستغرق بعض الوقت في أول مرة)")
        print("="*70 + "\n")
        return False


def main():
    """Main function - updated and enhanced"""
    print("\n" + "="*70)
    print("🤖 مساعد الدراسة الذكي - Smart Study Assistant")
    print("📦 النسخة المحسّنة v3.0")
    print("="*70 + "\n")

    # Create directories
    setup_directories()

    # 🆕 Check cache status
    cache_exists = check_cache_status()

    # Check for data existence
    db_manager = DatabaseManager()
    biology_content = db_manager.get_textbook_content("biology")
    arabic_content = db_manager.get_textbook_content("arabic")

    # If the database is empty, process PDF
    if not biology_content and not arabic_content:
        print("📚 قاعدة البيانات فارغة، جاري معالجة الكتب...\n")
        process_pdfs()
        verify_database()
    else:
        print(f"✅ قاعدة البيانات جاهزة!")
        print(f"   • الأحياء: {len(biology_content)} قطعة")
        print(f"   • العربي: {len(arabic_content)} قطعة\n")

    # Run the bot
    print("="*70)
    print("🚀 تشغيل Telegram Bot...")
    print("="*70 + "\n")

    bot = StudyAssistantBot(TELEGRAM_TOKEN)

    # Run the reminder system
    print("⏰ تشغيل نظام التذكيرات...")
    reminder_system = ReminderSystem(bot.updater.bot, db_manager)
    reminder_system.start()
    print("✅ نظام التذكيرات يعمل!\n")

    print("="*70)
    print("✅ البوت يعمل الآن بكامل الميزات!")
    print("="*70)
    print("\n🎯 **الميزات الجديدة:**")
    print("   1. ✅ تحسين دقة الإجابات")
    print("   2. 🎨 واجهة مستخدم محسّنة")
    print("   3. ⏰ نظام تذكيرات ذكي")
    print("   4. 📋 إدارة مهام متقدمة")
    print("   5. 🎯 اختبارات تفاعلية")
    print("   6. 🔍 فلترة ذكية للمواد")
    print("   7. 💾 حفظ الـ cache (لا إعادة معالجة)")
    print("   8. 📊 إحصائيات دقيقة للمهام\n")

    if cache_exists:
        print("💡 تم استخدام الـ cache المحفوظ - البوت جاهز فوراً!\n")
    else:
        print("💡 تم بناء الفهرس وحفظه - المرة القادمة ستكون أسرع!\n")

    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n\n⏹️ إيقاف البوت...")
        reminder_system.stop()
        print("✅ تم الإيقاف بنجاح")


if __name__ == "__main__":
    main()