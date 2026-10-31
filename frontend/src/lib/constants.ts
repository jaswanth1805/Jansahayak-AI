export const LANGUAGES = [
  { code: 'en', name: 'English', nativeName: 'English', flag: '🇮🇳' },
  { code: 'hi', name: 'Hindi', nativeName: 'हिंदी', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', nativeName: 'తెలుగు', flag: '🇮🇳' },
] as const;

export type SupportedLanguage = (typeof LANGUAGES)[number]['code'];

export const SCHEME_CATEGORIES = [
  'Agriculture & Rural Development',
  'Education & Learning',
  'Health & Wellness',
  'Financial Inclusion',
  'Housing',
  'Women & Child Development',
  'Employment & Skills',
  'Social Security & Welfare',
  'Business & Entrepreneurship',
  'Digital Services',
];

export const INDIAN_STATES = [
  'Andhra Pradesh',
  'Arunachal Pradesh',
  'Assam',
  'Bihar',
  'Chhattisgarh',
  'Goa',
  'Gujarat',
  'Haryana',
  'Himachal Pradesh',
  'Jharkhand',
  'Karnataka',
  'Kerala',
  'Madhya Pradesh',
  'Maharashtra',
  'Manipur',
  'Meghalaya',
  'Mizoram',
  'Nagaland',
  'Odisha',
  'Punjab',
  'Rajasthan',
  'Sikkim',
  'Tamil Nadu',
  'Telangana',
  'Tripura',
  'Uttar Pradesh',
  'Uttarakhand',
  'West Bengal',
  'Andaman and Nicobar Islands',
  'Chandigarh',
  'Dadra and Nagar Haveli',
  'Daman and Diu',
  'Delhi',
  'Jammu and Kashmir',
  'Ladakh',
  'Lakshadweep',
  'Puducherry',
];

export const SUGGESTED_QUESTIONS: Record<string, string[]> = {
  en: [
    'What scholarships are available for engineering students?',
    'How can farmers apply for PM-KISAN scheme?',
    'What health schemes are available for women?',
    'Tell me about Pradhan Mantri Awas Yojana',
    'What business loans are available for small entrepreneurs?',
  ],
  hi: [
    'इंजीनियरिंग छात्रों के लिए कौन सी छात्रवृत्ति उपलब्ध है?',
    'किसान PM-KISAN योजना के लिए कैसे आवेदन करें?',
    'महिलाओं के लिए कौन सी स्वास्थ्य योजनाएं हैं?',
    'प्रधानमंत्री आवास योजना के बारे में बताएं',
    'छोटे उद्यमियों के लिए कौन से व्यावसायिक ऋण उपलब्ध हैं?',
  ],
  te: [
    'ఇంజినీరింగ్ విద్యార్థులకు ఏ స్కాలర్షిప్లు అందుబాటులో ఉన్నాయి?',
    'రైతులు PM-KISAN పథకానికి ఎలా దరఖాస్తు చేసుకోవాలి?',
    'మహిళలకు ఏ ఆరోగ్య పథకాలు ఉన్నాయి?',
    'ప్రధాన మంత్రి ఆవాస్ యోజన గురించి చెప్పండి',
    'చిన్న వ్యాపారుల కోసం ఏ వ్యాపార రుణాలు అందుబాటులో ఉన్నాయి?',
  ],
};
