import { createContext, useContext, useState } from "react";

const LANGS = ["en-IN", "hi", "ta", "te"];

const DICT = {
  "en-IN": {
    "lang.name": "English",
    "app.title": "Waypoint",
    "app.tagline": "budget-honest trip planning",
    "step.intake": "Trip", "step.reality": "Reality check", "step.select_flight": "Flight",
    "step.select_hotel": "Hotel", "step.select_package": "Package", "step.select_guide": "Guide",
    "step.review": "Confirm",

    "intake.title": "Where to, and what can you spend?",
    "intake.subtitle": "Set your budget once. Before anything is searched, you'll see whether it's realistic for this trip — not just whether it's technically possible.",
    "intake.from": "From", "intake.to": "To", "intake.depart": "Depart", "intake.return": "Return",
    "intake.travelers": "Travelers", "intake.language": "Language",
    "intake.budget": "Budget cap (₹, total for the trip)",
    "intake.submit": "Check my budget →", "intake.checking": "Checking…",

    "reality.no_data_title": "No market data for this destination",
    "reality.no_data_fallback": "This destination isn't in our dataset yet, so there's no market comparison — but you can still plan the trip.",
    "reality.plan_anyway": "Plan anyway →", "reality.starting": "Starting…",
    "reality.label": "Reality check",
    "reality.question": "Is {amt} realistic here?",
    "reality.verdict.comfortable": "Comfortable", "reality.verdict.tight": "Tight", "reality.verdict.unrealistic": "Unrealistic",
    "reality.gap_above": "{pct}% above the typical cost for a trip like this",
    "reality.gap_below": "{pct}% below the typical cost for a trip like this",
    "reality.typical_range": "typical range",
    "reality.your_budget": "Your budget", "reality.closest_pkg": "Closest real package:",
    "reality.no_fit": "No real package fits this yet.",
    "reality.typical_trip": "Typical trip",
    "reality.sample": "from {n} real package(s), {level}-level",
    "reality.rec_tight": "{amt} would put you in typical range",
    "reality.rec_comfortable": "{amt} would cover this comfortably",
    "reality.rec_days": "~{n} day(s) fits this budget better",
    "reality.adjust": "← Adjust", "reality.continue": "Continue with this budget →",

    "flight.title": "Choose a flight", "flight.subtitle": "Sorted cheapest first.",
    "flight.confidence": "{pct}% confidence",

    "hotel.title": "Choose a hotel", "hotel.subtitle": "Total for your whole stay.",
    "hotel.nights": "night(s)", "hotel.per_night": "/night",

    "pkg.title": "Your package",
    "pkg.subtitle": "Swap anything with a \"swap\" tag — the total updates live and re-checks your budget.",
    "pkg.day": "Day {n}", "pkg.swap": "swap", "pkg.loading_alts": "Loading alternatives…",
    "pkg.no_alts": "No alternatives available for this item right now.",
    "pkg.continue": "Continue to guide →",

    "guide.title": "Add a local guide?",
    "guide.subtitle": "Matched by language and specialisation. Optional.",
    "guide.finding": "Finding guides…",
    "guide.none": "No guides matched for this destination and language yet.",
    "guide.speaks": "speaks", "guide.per_day": "/day", "guide.book": "Book {n}d",
    "guide.days_label": "Days:", "guide.skip": "Skip guide, continue →",
    "guide.filter_all": "All specialisations",
    "guide.spec.food": "Food", "guide.spec.heritage": "Heritage", "guide.spec.photography": "Photography",
    "guide.spec.religious": "Religious", "guide.spec.shopping": "Shopping", "guide.spec.trekking": "Trekking",
    "guide.spec.wildlife": "Wildlife", "guide.spec.accessibility": "Accessibility",
    "guide.lang_match": "speaks your language",
    "guide.top_rated": "top rated",

    "negotiate.title": "This would go over budget",
    "negotiate.subtitle": "Nothing has been added. Pick how you'd like to handle it.",
    "negotiate.approve_overage": "Approve the extra {amt} for {item}",
    "negotiate.swap_cheaper": "Swap {item} for a cheaper alternative",
    "negotiate.remove_item": "Drop {item} and keep the rest",
    "negotiate.raise_cap": "Raise my overall trip budget",
    "negotiate.new_cap_placeholder": "New total budget (₹)",
    "negotiate.set": "Set",

    "review.confirmed_badge": "✓ Confirmed", "review.locked_in": "Trip locked in",
    "review.final": "Final total {total} of your {cap} cap — never crossed.",
    "review.title": "Review & confirm", "review.subtitle": "Nothing is booked until you confirm.",
    "review.flight": "Flight", "review.hotel": "Hotel", "review.guide": "Guide",
    "review.guide_not_booked": "Not booked", "review.total": "Total",
    "review.confirm": "Confirm trip →", "review.confirming": "Confirming…",

    "ledger.running_total": "Running total", "ledger.cap": "cap",
    "trace.show": "Show agent trace ({n})", "trace.hide": "Hide agent trace ({n})",
    "app.plan_another": "Plan another trip",
  },
  "hi": {
    "lang.name": "हिन्दी",
    "app.title": "Waypoint", "app.tagline": "बजट-ईमानदार यात्रा योजना",
    "step.intake": "यात्रा", "step.reality": "बजट जांच", "step.select_flight": "फ्लाइट",
    "step.select_hotel": "होटल", "step.select_package": "पैकेज", "step.select_guide": "गाइड",
    "step.review": "पुष्टि करें",

    "intake.title": "कहाँ जाना है, और कितना खर्च कर सकते हैं?",
    "intake.subtitle": "अपना बजट एक बार सेट करें। कुछ भी खोजने से पहले, आप देखेंगे कि यह इस यात्रा के लिए वास्तविक है या नहीं।",
    "intake.from": "कहाँ से", "intake.to": "कहाँ", "intake.depart": "जाने की तारीख", "intake.return": "वापसी",
    "intake.travelers": "यात्री", "intake.language": "भाषा",
    "intake.budget": "बजट सीमा (₹, पूरी यात्रा के लिए)",
    "intake.submit": "मेरा बजट जांचें →", "intake.checking": "जांच रहे हैं…",

    "reality.no_data_title": "इस गंतव्य के लिए बाज़ार डेटा नहीं है",
    "reality.no_data_fallback": "यह गंतव्य अभी हमारे डेटा में नहीं है, इसलिए तुलना संभव नहीं — पर आप फिर भी यात्रा की योजना बना सकते हैं।",
    "reality.plan_anyway": "फिर भी योजना बनाएं →", "reality.starting": "शुरू हो रहा है…",
    "reality.label": "बजट जांच",
    "reality.question": "क्या यहाँ {amt} वास्तविक है?",
    "reality.verdict.comfortable": "आरामदायक", "reality.verdict.tight": "तंग", "reality.verdict.unrealistic": "अवास्तविक",
    "reality.gap_above": "इस तरह की यात्रा की सामान्य लागत से {pct}% अधिक",
    "reality.gap_below": "इस तरह की यात्रा की सामान्य लागत से {pct}% कम",
    "reality.typical_range": "सामान्य सीमा",
    "reality.your_budget": "आपका बजट", "reality.closest_pkg": "सबसे नज़दीकी असली पैकेज:",
    "reality.no_fit": "इस बजट में फिट होने वाला कोई असली पैकेज नहीं है।",
    "reality.typical_trip": "सामान्य यात्रा",
    "reality.sample": "{n} असली पैकेज पर आधारित, {level}-स्तर",
    "reality.rec_tight": "{amt} से आप सामान्य सीमा में आ जाएंगे",
    "reality.rec_comfortable": "{amt} से यह आराम से कवर हो जाएगा",
    "reality.rec_days": "~{n} दिन इस बजट में बेहतर फिट होंगे",
    "reality.adjust": "← बदलें", "reality.continue": "इस बजट के साथ आगे बढ़ें →",

    "flight.title": "फ्लाइट चुनें", "flight.subtitle": "सबसे सस्ता पहले।",
    "flight.confidence": "{pct}% विश्वसनीयता",

    "hotel.title": "होटल चुनें", "hotel.subtitle": "पूरे ठहराव के लिए कुल।",
    "hotel.nights": "रात", "hotel.per_night": "/रात",

    "pkg.title": "आपका पैकेज",
    "pkg.subtitle": "\"swap\" टैग वाली किसी भी चीज़ को बदलें — कुल राशि तुरंत अपडेट होगी और बजट फिर से जांचा जाएगा।",
    "pkg.day": "दिन {n}", "pkg.swap": "बदलें", "pkg.loading_alts": "विकल्प लोड हो रहे हैं…",
    "pkg.no_alts": "अभी इसके लिए कोई विकल्प उपलब्ध नहीं है।",
    "pkg.continue": "गाइड की ओर बढ़ें →",

    "guide.title": "स्थानीय गाइड जोड़ें?",
    "guide.subtitle": "भाषा और विशेषज्ञता के आधार पर मिलान। वैकल्पिक।",
    "guide.finding": "गाइड खोजे जा रहे हैं…",
    "guide.none": "इस गंतव्य और भाषा के लिए अभी कोई गाइड नहीं मिला।",
    "guide.speaks": "बोलते हैं", "guide.per_day": "/दिन", "guide.book": "{n}दिन बुक करें",
    "guide.days_label": "दिन:", "guide.skip": "गाइड छोड़ें, आगे बढ़ें →",
    "guide.filter_all": "सभी विशेषज्ञताएं",
    "guide.spec.food": "भोजन", "guide.spec.heritage": "धरोहर", "guide.spec.photography": "फोटोग्राफी",
    "guide.spec.religious": "धार्मिक", "guide.spec.shopping": "खरीदारी", "guide.spec.trekking": "ट्रेकिंग",
    "guide.spec.wildlife": "वन्यजीव", "guide.spec.accessibility": "सुगमता",
    "guide.lang_match": "आपकी भाषा बोलते हैं",
    "guide.top_rated": "सर्वोच्च रेटेड",

    "negotiate.title": "यह बजट से अधिक हो जाएगा",
    "negotiate.subtitle": "कुछ भी नहीं जोड़ा गया है। चुनें कि आप कैसे आगे बढ़ना चाहते हैं।",
    "negotiate.approve_overage": "{item} के लिए अतिरिक्त {amt} स्वीकृत करें",
    "negotiate.swap_cheaper": "{item} को सस्ते विकल्प से बदलें",
    "negotiate.remove_item": "{item} हटाएं और बाकी रखें",
    "negotiate.raise_cap": "मेरा कुल यात्रा बजट बढ़ाएं",
    "negotiate.new_cap_placeholder": "नया कुल बजट (₹)",
    "negotiate.set": "सेट करें",

    "review.confirmed_badge": "✓ पुष्ट", "review.locked_in": "यात्रा पक्की हो गई",
    "review.final": "अंतिम कुल {total}, आपकी {cap} सीमा में — कभी पार नहीं हुई।",
    "review.title": "समीक्षा और पुष्टि", "review.subtitle": "पुष्टि करने तक कुछ भी बुक नहीं होता।",
    "review.flight": "फ्लाइट", "review.hotel": "होटल", "review.guide": "गाइड",
    "review.guide_not_booked": "बुक नहीं किया गया", "review.total": "कुल",
    "review.confirm": "यात्रा पुष्ट करें →", "review.confirming": "पुष्टि हो रही है…",

    "ledger.running_total": "चालू कुल", "ledger.cap": "सीमा",
    "trace.show": "एजेंट ट्रेस दिखाएं ({n})", "trace.hide": "एजेंट ट्रेस छिपाएं ({n})",
    "app.plan_another": "एक और यात्रा की योजना बनाएं",
  },
  "ta": {
    "lang.name": "தமிழ்",
    "app.title": "Waypoint", "app.tagline": "பட்ஜெட்-நேர்மையான பயண திட்டமிடல்",
    "step.intake": "பயணம்", "step.reality": "பட்ஜெட் சரிபார்ப்பு", "step.select_flight": "விமானம்",
    "step.select_hotel": "ஹோட்டல்", "step.select_package": "தொகுப்பு", "step.select_guide": "வழிகாட்டி",
    "step.review": "உறுதிப்படுத்தவும்",

    "intake.title": "எங்கே செல்கிறீர்கள், எவ்வளவு செலவிட முடியும்?",
    "intake.subtitle": "உங்கள் பட்ஜெட்டை ஒருமுறை அமைக்கவும். எதையும் தேடுவதற்கு முன், இது இந்த பயணத்திற்கு நடைமுறைக்குச் சாத்தியமா என்பதைப் பார்ப்பீர்கள்.",
    "intake.from": "இருந்து", "intake.to": "செல்லும் இடம்", "intake.depart": "புறப்படும் தேதி", "intake.return": "திரும்பும் தேதி",
    "intake.travelers": "பயணிகள்", "intake.language": "மொழி",
    "intake.budget": "பட்ஜெட் வரம்பு (₹, முழு பயணத்திற்கும்)",
    "intake.submit": "என் பட்ஜெட்டை சரிபார்க்கவும் →", "intake.checking": "சரிபார்க்கிறது…",

    "reality.no_data_title": "இந்த இடத்திற்கு சந்தை தரவு இல்லை",
    "reality.no_data_fallback": "இந்த இடம் இன்னும் எங்கள் தரவில் இல்லை, எனவே ஒப்பீடு இல்லை — ஆனால் நீங்கள் இன்னும் பயணத்தை திட்டமிடலாம்.",
    "reality.plan_anyway": "எப்படியும் திட்டமிடு →", "reality.starting": "தொடங்குகிறது…",
    "reality.label": "பட்ஜெட் சரிபார்ப்பு",
    "reality.question": "இங்கே {amt} நடைமுறைக்குச் சாத்தியமா?",
    "reality.verdict.comfortable": "வசதியானது", "reality.verdict.tight": "நெருக்கமானது", "reality.verdict.unrealistic": "நடைமுறைக்குச் சாத்தியமற்றது",
    "reality.gap_above": "இதுபோன்ற பயணத்தின் சாதாரண செலவை விட {pct}% அதிகம்",
    "reality.gap_below": "இதுபோன்ற பயணத்தின் சாதாரண செலவை விட {pct}% குறைவு",
    "reality.typical_range": "வழக்கமான வரம்பு",
    "reality.your_budget": "உங்கள் பட்ஜெட்", "reality.closest_pkg": "நெருக்கமான உண்மையான தொகுப்பு:",
    "reality.no_fit": "இந்த பட்ஜெட்டில் பொருந்தும் உண்மையான தொகுப்பு இல்லை.",
    "reality.typical_trip": "வழக்கமான பயணம்",
    "reality.sample": "{n} உண்மையான தொகுப்பு(கள்) அடிப்படையில், {level}-நிலை",
    "reality.rec_tight": "{amt} இருந்தால் வழக்கமான வரம்பில் இருப்பீர்கள்",
    "reality.rec_comfortable": "{amt} இதை வசதியாக ஈடுசெய்யும்",
    "reality.rec_days": "~{n} நாள்(கள்) இந்த பட்ஜெட்டிற்கு மேலும் பொருந்தும்",
    "reality.adjust": "← மாற்று", "reality.continue": "இந்த பட்ஜெட்டுடன் தொடரவும் →",

    "flight.title": "விமானத்தை தேர்வு செய்யவும்", "flight.subtitle": "மலிவானது முதலில்.",
    "flight.confidence": "{pct}% நம்பகத்தன்மை",

    "hotel.title": "ஹோட்டலை தேர்வு செய்யவும்", "hotel.subtitle": "முழு தங்குமிடத்திற்கான மொத்தம்.",
    "hotel.nights": "இரவு(கள்)", "hotel.per_night": "/இரவு",

    "pkg.title": "உங்கள் தொகுப்பு",
    "pkg.subtitle": "\"swap\" குறிச்சொல் உள்ள எதையும் மாற்றவும் — மொத்தம் உடனடியாக புதுப்பிக்கப்பட்டு பட்ஜெட் மீண்டும் சரிபார்க்கப்படும்.",
    "pkg.day": "நாள் {n}", "pkg.swap": "மாற்று", "pkg.loading_alts": "மாற்றுகள் ஏற்றப்படுகின்றன…",
    "pkg.no_alts": "இதற்கு தற்போது மாற்றுகள் இல்லை.",
    "pkg.continue": "வழிகாட்டிக்கு தொடரவும் →",

    "guide.title": "உள்ளூர் வழிகாட்டியை சேர்க்கவா?",
    "guide.subtitle": "மொழி மற்றும் நிபுணத்துவத்தின் அடிப்படையில் பொருத்தப்பட்டது. விருப்பத்தேர்வு.",
    "guide.finding": "வழிகாட்டிகள் தேடப்படுகின்றன…",
    "guide.none": "இந்த இடம் மற்றும் மொழிக்கு இன்னும் வழிகாட்டி இல்லை.",
    "guide.speaks": "பேசுகிறார்", "guide.per_day": "/நாள்", "guide.book": "{n}நாள் முன்பதிவு",
    "guide.days_label": "நாட்கள்:", "guide.skip": "வழிகாட்டியை தவிர்த்து தொடரவும் →",
    "guide.filter_all": "அனைத்து நிபுணத்துவங்கள்",
    "guide.spec.food": "உணவு", "guide.spec.heritage": "பாரம்பரியம்", "guide.spec.photography": "புகைப்படம்",
    "guide.spec.religious": "மத", "guide.spec.shopping": "ஷாப்பிங்", "guide.spec.trekking": "மலையேற்றம்",
    "guide.spec.wildlife": "வனவிலங்கு", "guide.spec.accessibility": "அணுகல்தன்மை",
    "guide.lang_match": "உங்கள் மொழி பேசுகிறார்",
    "guide.top_rated": "சிறந்த மதிப்பீடு",

    "negotiate.title": "இது பட்ஜெட்டை மீறும்",
    "negotiate.subtitle": "இன்னும் எதுவும் சேர்க்கப்படவில்லை. எப்படி தொடர விரும்புகிறீர்கள் என்பதைத் தேர்வு செய்யவும்.",
    "negotiate.approve_overage": "{item}க்கான கூடுதல் {amt} ஐ அங்கீகரிக்கவும்",
    "negotiate.swap_cheaper": "{item} ஐ மலிவான மாற்றீட்டுடன் மாற்றவும்",
    "negotiate.remove_item": "{item} ஐ நீக்கி மீதமுள்ளதை வைத்திருங்கள்",
    "negotiate.raise_cap": "எனது மொத்த பயண பட்ஜெட்டை உயர்த்தவும்",
    "negotiate.new_cap_placeholder": "புதிய மொத்த பட்ஜெட் (₹)",
    "negotiate.set": "அமை",

    "review.confirmed_badge": "✓ உறுதி செய்யப்பட்டது", "review.locked_in": "பயணம் உறுதி செய்யப்பட்டது",
    "review.final": "இறுதி மொத்தம் {total}, உங்கள் {cap} வரம்பில் — ஒருபோதும் மீறவில்லை.",
    "review.title": "மதிப்பாய்வு & உறுதிப்படுத்தல்", "review.subtitle": "நீங்கள் உறுதிப்படுத்தும் வரை எதுவும் பதிவு செய்யப்படாது.",
    "review.flight": "விமானம்", "review.hotel": "ஹோட்டல்", "review.guide": "வழிகாட்டி",
    "review.guide_not_booked": "முன்பதிவு செய்யப்படவில்லை", "review.total": "மொத்தம்",
    "review.confirm": "பயணத்தை உறுதிப்படுத்தவும் →", "review.confirming": "உறுதிப்படுத்துகிறது…",

    "ledger.running_total": "நடப்பு மொத்தம்", "ledger.cap": "வரம்பு",
    "trace.show": "ஏஜென்ட் தடத்தை காட்டு ({n})", "trace.hide": "ஏஜென்ட் தடத்தை மறை ({n})",
    "app.plan_another": "மற்றொரு பயணத்தை திட்டமிடு",
  },
  "te": {
    "lang.name": "తెలుగు",
    "app.title": "Waypoint", "app.tagline": "బడ్జెట్-నిజాయితీ ప్రయాణ ప్రణాళిక",
    "step.intake": "ప్రయాణం", "step.reality": "బడ్జెట్ తనిఖీ", "step.select_flight": "విమానం",
    "step.select_hotel": "హోటల్", "step.select_package": "ప్యాకేజీ", "step.select_guide": "గైడ్",
    "step.review": "నిర్ధారించండి",

    "intake.title": "ఎక్కడికి వెళ్తున్నారు, ఎంత ఖర్చు చేయగలరు?",
    "intake.subtitle": "మీ బడ్జెట్‌ను ఒకసారి సెట్ చేయండి. ఏదైనా వెతకడానికి ముందు, ఇది ఈ ప్రయాణానికి వాస్తవికమేనా అని చూస్తారు.",
    "intake.from": "నుండి", "intake.to": "వరకు", "intake.depart": "బయలుదేరే తేదీ", "intake.return": "తిరిగి వచ్చే తేదీ",
    "intake.travelers": "ప్రయాణికులు", "intake.language": "భాష",
    "intake.budget": "బడ్జెట్ పరిమితి (₹, మొత్తం ప్రయాణానికి)",
    "intake.submit": "నా బడ్జెట్‌ను తనిఖీ చేయండి →", "intake.checking": "తనిఖీ చేస్తోంది…",

    "reality.no_data_title": "ఈ గమ్యస్థానానికి మార్కెట్ డేటా లేదు",
    "reality.no_data_fallback": "ఈ గమ్యస్థానం ఇంకా మా డేటాలో లేదు, కాబట్టి పోలిక లేదు — కానీ మీరు ఇప్పటికీ ప్రయాణాన్ని ప్లాన్ చేసుకోవచ్చు.",
    "reality.plan_anyway": "అయినా ప్లాన్ చేయండి →", "reality.starting": "ప్రారంభమవుతోంది…",
    "reality.label": "బడ్జెట్ తనిఖీ",
    "reality.question": "ఇక్కడ {amt} వాస్తవికమేనా?",
    "reality.verdict.comfortable": "సౌకర్యవంతం", "reality.verdict.tight": "ఇరుకైనది", "reality.verdict.unrealistic": "అవాస్తవికం",
    "reality.gap_above": "ఇలాంటి ప్రయాణం సాధారణ ఖర్చు కంటే {pct}% ఎక్కువ",
    "reality.gap_below": "ఇలాంటి ప్రయాణం సాధారణ ఖర్చు కంటే {pct}% తక్కువ",
    "reality.typical_range": "సాధారణ పరిధి",
    "reality.your_budget": "మీ బడ్జెట్", "reality.closest_pkg": "దగ్గరి నిజమైన ప్యాకేజీ:",
    "reality.no_fit": "ఈ బడ్జెట్‌లో సరిపోయే నిజమైన ప్యాకేజీ లేదు.",
    "reality.typical_trip": "సాధారణ ప్రయాణం",
    "reality.sample": "{n} నిజమైన ప్యాకేజీ(ల) ఆధారంగా, {level}-స్థాయి",
    "reality.rec_tight": "{amt} ఉంటే సాధారణ పరిధిలోకి వస్తారు",
    "reality.rec_comfortable": "{amt} దీన్ని సౌకర్యవంతంగా కవర్ చేస్తుంది",
    "reality.rec_days": "~{n} రోజు(లు) ఈ బడ్జెట్‌కి బాగా సరిపోతుంది",
    "reality.adjust": "← మార్చండి", "reality.continue": "ఈ బడ్జెట్‌తో కొనసాగండి →",

    "flight.title": "విమానాన్ని ఎంచుకోండి", "flight.subtitle": "చౌకైనది మొదట.",
    "flight.confidence": "{pct}% విశ్వసనీయత",

    "hotel.title": "హోటల్‌ను ఎంచుకోండి", "hotel.subtitle": "మీ మొత్తం బసకు మొత్తం.",
    "hotel.nights": "రాత్రి(లు)", "hotel.per_night": "/రాత్రి",

    "pkg.title": "మీ ప్యాకేజీ",
    "pkg.subtitle": "\"swap\" ట్యాగ్ ఉన్న దేనినైనా మార్చండి — మొత్తం తక్షణమే నవీకరించబడి బడ్జెట్ మళ్లీ తనిఖీ చేయబడుతుంది.",
    "pkg.day": "రోజు {n}", "pkg.swap": "మార్చండి", "pkg.loading_alts": "ప్రత్యామ్నాయాలు లోడ్ అవుతున్నాయి…",
    "pkg.no_alts": "దీనికి ప్రస్తుతం ప్రత్యామ్నాయాలు లేవు.",
    "pkg.continue": "గైడ్‌కి కొనసాగండి →",

    "guide.title": "స్థానిక గైడ్‌ను జోడించాలా?",
    "guide.subtitle": "భాష మరియు నైపుణ్యం ఆధారంగా సరిపోల్చబడింది. ఐచ్ఛికం.",
    "guide.finding": "గైడ్‌లు కనుగొనబడుతున్నారు…",
    "guide.none": "ఈ గమ్యస్థానం మరియు భాషకు ఇంకా గైడ్ లేరు.",
    "guide.speaks": "మాట్లాడతారు", "guide.per_day": "/రోజు", "guide.book": "{n}రోజులు బుక్ చేయండి",
    "guide.days_label": "రోజులు:", "guide.skip": "గైడ్‌ను వదిలి కొనసాగండి →",
    "guide.filter_all": "అన్ని నైపుణ్యాలు",
    "guide.spec.food": "ఆహారం", "guide.spec.heritage": "వారసత్వం", "guide.spec.photography": "ఫోటోగ్రఫీ",
    "guide.spec.religious": "మతపరమైన", "guide.spec.shopping": "షాపింగ్", "guide.spec.trekking": "ట్రెక్కింగ్",
    "guide.spec.wildlife": "వన్యప్రాణులు", "guide.spec.accessibility": "అందుబాటు",
    "guide.lang_match": "మీ భాష మాట్లాడతారు",
    "guide.top_rated": "అత్యధిక రేటింగ్",

    "negotiate.title": "ఇది బడ్జెట్‌ను మించిపోతుంది",
    "negotiate.subtitle": "ఇంకా ఏమీ జోడించలేదు. మీరు ఎలా కొనసాగాలనుకుంటున్నారో ఎంచుకోండి.",
    "negotiate.approve_overage": "{item} కోసం అదనపు {amt}ని ఆమోదించండి",
    "negotiate.swap_cheaper": "{item}ని చౌకైన ప్రత్యామ్నాయంతో మార్చండి",
    "negotiate.remove_item": "{item}ని తీసివేసి మిగిలినవి ఉంచండి",
    "negotiate.raise_cap": "నా మొత్తం ప్రయాణ బడ్జెట్‌ను పెంచండి",
    "negotiate.new_cap_placeholder": "కొత్త మొత్తం బడ్జెట్ (₹)",
    "negotiate.set": "సెట్ చేయండి",

    "review.confirmed_badge": "✓ నిర్ధారించబడింది", "review.locked_in": "ప్రయాణం ఖరారైంది",
    "review.final": "తుది మొత్తం {total}, మీ {cap} పరిమితిలో — ఎప్పుడూ దాటలేదు.",
    "review.title": "సమీక్ష & నిర్ధారణ", "review.subtitle": "మీరు నిర్ధారించే వరకు ఏమీ బుక్ చేయబడదు.",
    "review.flight": "విమానం", "review.hotel": "హోటల్", "review.guide": "గైడ్",
    "review.guide_not_booked": "బుక్ చేయలేదు", "review.total": "మొత్తం",
    "review.confirm": "ప్రయాణాన్ని నిర్ధారించండి →", "review.confirming": "నిర్ధారిస్తోంది…",

    "ledger.running_total": "ప్రస్తుత మొత్తం", "ledger.cap": "పరిమితి",
    "trace.show": "ఏజెంట్ ట్రేస్ చూపించు ({n})", "trace.hide": "ఏజెంట్ ట్రేస్ దాచు ({n})",
    "app.plan_another": "మరో ప్రయాణాన్ని ప్లాన్ చేయండి",
  },
};

const I18nContext = createContext(null);

export function I18nProvider({ children, initialLang = "en-IN" }) {
  const [lang, setLang] = useState(initialLang);

  function t(key, vars) {
    let str = DICT[lang]?.[key] ?? DICT["en-IN"][key] ?? key;
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        str = str.replaceAll(`{${k}}`, v);
      }
    }
    return str;
  }

  return (
    <I18nContext.Provider value={{ lang, setLang, t, LANGS }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useT() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useT must be used inside I18nProvider");
  return ctx;
}

export { LANGS, DICT };
