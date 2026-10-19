"""Small auditable finance vocabulary; language normalization never invents facts."""
import re

PHRASES = {
    'বকেয়া': 'overdue', 'বকেয়া': 'overdue', 'পাওনা': 'receivable', 'কাস্টমার': 'customer',
    'গ্রাহক': 'customer', 'অর্ধেক': 'half', 'আধা': 'half', 'ঋণ ছাড়া': 'without borrowing',
    'ঋণ ছাড়া': 'without borrowing', 'ধার ছাড়া': 'without borrowing', 'ধার ছাড়া': 'without borrowing',
    'ঋণ': 'loan', 'খরচ': 'expenses', 'বিক্রি': 'sales', 'বিক্রয়': 'sales', 'বিক্রয়': 'sales',
    'কমে': 'decline', 'বাড়ে': 'increase', 'বাড়ে': 'increase', 'বেড়েছে': 'increase', 'বেড়েছে': 'increase',
    'সাপ্লায়ার': 'supplier', 'সাপ্লায়ার': 'supplier', 'সরবরাহকারী': 'supplier', 'বেতন': 'payroll',
    'রিজার্ভ': 'reserve', 'নগদ': 'cash', 'টাকা': 'money', 'অগ্রাধিকার': 'prioritize',
    'কত': 'how much', 'কেন': 'why', 'কোন': 'which', 'পরিশোধ': 'payment', 'ফুটবল': 'football',
    'বিশ্বকাপ': 'world cup', 'আবহাওয়া': 'weather', 'নিরাপদ': 'safe',
    'যদি': 'what if',
    'ঋণ নেব না': 'without borrowing', 'ঋণ নেবো না': 'without borrowing', 'লোন ছাড়া': 'without borrowing',
    'লোন ছাড়া': 'without borrowing', 'ধার নেব না': 'without borrowing',
    'জানুয়ারি': 'january', 'ফেব্রুয়ারি': 'february', 'মার্চ': 'march', 'এপ্রিল': 'april', 'মে': 'may',
    'জুন': 'june', 'জুলাই': 'july', 'আগস্ট': 'august', 'সেপ্টেম্বর': 'september',
    'অক্টোবর': 'october', 'নভেম্বর': 'november', 'ডিসেম্বর': 'december',
}
BANGLISH = {
    'bokeya': 'overdue', 'bokea': 'overdue', 'pao na': 'receivable', 'paona': 'receivable',
    'ordhek': 'half', 'ardhek': 'half', 'adha': 'half', 'khoroch': 'expenses', 'khoroc': 'expenses',
    'bikri': 'sales', 'beton': 'payroll', 'taka': 'money', 'koto': 'how much', 'keno': 'why',
    'loan chara': 'without borrowing', 'rin chara': 'without borrowing', 'dhar chara': 'without borrowing',
    'age dibo': 'prioritize', 'age debo': 'prioritize', 'komle': 'decline', 'bereche': 'increase',
    'jodi': 'what if',
    'loan nibo na': 'without borrowing', 'rin nibo na': 'without borrowing',
}


def normalize_question(question):
    text = question.casefold().translate(str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789'))
    for source, target in sorted(PHRASES.items(),key=lambda item:-len(item[0])):
        text = text.replace(source, ' '+target+' ')
    for source, target in BANGLISH.items():
        text = re.sub(r'\b'+re.escape(source)+r'\b', target, text)
    return re.sub(r'\s+', ' ', text).strip()


def effective_question(question, history):
    text = normalize_question(question)
    partial = bool(re.search(r'\bhalf\b', text))
    explicit = bool(re.search(r'\b(cash|reserve|invoice|overdue|receivable|customer|supplier|expenses|sales|loan|payroll)\b', text))
    if partial or (not explicit and re.search(r'\b(only|that|this|those|it|instead|then|what if)\b', text)):
        pattern = r'\b(invoice|overdue|receivable|customer)\b' if partial else r'\b(cash|reserve|invoice|overdue|receivable|customer|supplier|expenses|sales|loan|payroll)\b'
        prior = next((normalize_question(q) for q in history if re.search(pattern, normalize_question(q))), '')
        if prior:
            return text+'\nPrevious financial question: '+prior
    return text
