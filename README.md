# المساعد الذكي للأسئلة الشائعة

تطبيق Streamlit يجيب عن الأسئلة باستخدام نموذج Groq، ويبحث في الأسئلة الشائعة وملفات PDF/TXT المحلية.

## الإعداد والتشغيل على Windows

1. أنشئ مفتاحًا جديدًا من Groq بعد إلغاء المفتاح القديم الذي انكشف.
2. انسخ `.env.example` إلى `.env` وضع المفتاح الجديد بعد `GROQ_API_KEY=`.
3. فعّل البيئة وثبّت الاعتماديات:

   ```powershell
   .\faq_env\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. أعد بناء قاعدة المعرفة من `faqs.json` والملفات الاختيارية في `domain_data`:

   ```powershell
   python ingest.py
   ```

5. شغّل التطبيق:

   ```powershell
   streamlit run app.py
   ```

تحتاج أول عملية فهرسة إلى اتصال بالإنترنت لتنزيل نموذج التضمين. يمكن إضافة ملفات PDF أو ملفات TXT بترميز UTF-8 إلى `domain_data` ثم تشغيل `python ingest.py` مجددًا. ملف `MONGO_URI` غير مطلوب حاليًا لأن التطبيق لا يستخدم MongoDB.