"""Create four simple-language PDFs: Bengali/English speech and project guide.

Uses Chromium for proper Bengali shaping, and the installed Nirmala UI font.
The speeches follow the official four-slide deck; supporting guides are separate.
"""
import html
import json
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'static/submission/presentation-guides'
PREVIEW = ROOT/'test-results/bilingual-guides'


def p(value):
    return '<p>'+html.escape(value)+'</p>'


def section(title, *paragraphs):
    return '<h2>'+html.escape(title)+'</h2>'+''.join(p(value) for value in paragraphs)


def bullets(*items):
    return '<ul>'+''.join('<li>'+html.escape(item)+'</li>' for item in items)+'</ul>'


SPEECH_EN = [
    section('Slide 1 · Introduction · 0:00–0:15',
        'Hello, I am Meherab Hossain Talukder, a solo participant. FinPilot AI helps freelancers and small business owners answer a simple question: can I spend today and still pay my next important bill?'),
    section('Slide 2 · The solution · 0:15–1:15',
        'The problem is timing. A client may pay next week, but a bill may be due tomorrow. FinPilot separates money already received from money that is only expected.',
        'In Personal Mode, users enter their available cash, expected income, bills, and an emergency reserve. The dashboard shows their position. Its careful spending estimate does not count money that has not arrived.',
        'Users can then test four situations: a late payment, an extra expense, a savings transfer, or lower future income. The app compares the result with the original plan. These tests never change actual money records.',
        'The private AI Advisor explains the evidence and assumptions. Users can also export reports. Personal and business workspaces stay separate, and the app works on phones and computers.'),
    section('Slide 3 · A simple example · 1:15–2:10',
        'This example uses made-up data. We have eighteen thousand taka in cash, twelve thousand in upcoming bills, ten thousand expected from a client, and an eight-thousand-taka reserve target.',
        'If the client pays on time, ending cash is sixteen thousand. Now delay that payment by seven days. Ending cash is still sixteen thousand, but cash falls to six thousand before the payment arrives.',
        'That is two thousand below the reserve target. Cash has not become negative, but the safety buffer is too low. After bills, without counting future income, only six thousand remains. So the careful spending estimate is zero.',
        'FinPilot shows this timing risk before the user decides to spend.'),
    section('Slide 4 · AI, reliability and demo · 2:10–3:00',
        'The app calculates money figures first. Groq AI explains the evidence after that. AI cannot make payments or move money. If AI is unavailable, the app provides a clearly marked calculation-based explanation.',
        'The system uses Python, Django and PostgreSQL. I added Personal Mode and four personal scenarios to my existing small-business application. The documented release passed three hundred sixty-eight database tests, with browser checks at seven screen widths.',
        'Scan the QR code to try the free, account-free demo with made-up data. Its explanations are calculation-based; private workspaces can use Groq AI.',
        'FinPilot helps people understand their money before making a decision. Thank you.'),
]

SPEECH_BN = [
    section('স্লাইড ১ · পরিচয় · ০:০০–০:১৫',
        'আসসালামু আলাইকুম। আমি মো. মেহেরাব হোসেন তালুকদার। আমি একক প্রতিযোগী। আমার প্রজেক্ট FinPilot AI। এটি ফ্রিল্যান্সার ও ছোট ব্যবসার মালিককে বুঝতে সাহায্য করে—আজ খরচ করলে পরের জরুরি বিলটি দিতে পারব কি না।'),
    section('স্লাইড ২ · সমস্যার সমাধান · ০:১৫–১:১৫',
        'সমস্যাটি শুধু টাকার পরিমাণ নয়, টাকা আসার সময়ও। একজন ক্লায়েন্ট আগামী সপ্তাহে টাকা দিতে পারেন, কিন্তু বিল দিতে হবে আগামীকাল। FinPilot হাতে পাওয়া টাকা এবং ভবিষ্যতে আসতে পারে এমন টাকা আলাদা করে দেখায়।',
        'Personal Mode-এ ব্যবহারকারী হাতে থাকা টাকা, সম্ভাব্য আয়, বিল এবং জরুরি সঞ্চয়ের লক্ষ্য দেন। ড্যাশবোর্ডে বর্তমান অবস্থা দেখা যায়। কতটা খরচ করা যেতে পারে, তার হিসাব করার সময় এখনো না পাওয়া আয় ধরা হয় না।',
        'এরপর চারটি পরিস্থিতি পরীক্ষা করা যায়—আয় দেরিতে আসা, হঠাৎ বাড়তি খরচ, সঞ্চয়ে টাকা সরানো এবং ভবিষ্যৎ আয় কমে যাওয়া। আগের পরিকল্পনার সঙ্গে নতুন ফল তুলনা করা যায়। এতে আসল লেনদেন বদলায় না।',
        'প্রাইভেট AI Advisor তথ্য ও অনুমানগুলো বুঝিয়ে বলে। রিপোর্টও নামানো যায়। ব্যক্তিগত ও ব্যবসার তথ্য আলাদা থাকে। মোবাইল ও কম্পিউটার—দুই জায়গাতেই কাজ করে।'),
    section('স্লাইড ৩ · সহজ উদাহরণ · ১:১৫–২:১০',
        'এখানে সব তথ্য উদাহরণের জন্য তৈরি। হাতে আছে আঠারো হাজার টাকা। সামনে বিল বারো হাজার। একজন ক্লায়েন্টের কাছ থেকে আসতে পারে দশ হাজার। জরুরি তহবিলে রাখতে চাই আট হাজার টাকা।',
        'ক্লায়েন্ট সময়মতো টাকা দিলে শেষে থাকে ষোলো হাজার। এবার টাকা সাত দিন দেরিতে আসুক। শেষেও থাকে ষোলো হাজার, কিন্তু মাঝখানে হাতে থাকা টাকা নেমে যায় ছয় হাজারে।',
        'অর্থাৎ জরুরি তহবিলের লক্ষ্যের চেয়ে দুই হাজার কম। এটি ঋণাত্মক ব্যালেন্স নয়; নিরাপত্তার জন্য রাখতে চাওয়া টাকার ঘাটতি। ভবিষ্যৎ আয় বাদ দিয়ে বিল দেওয়ার পরও থাকে ছয় হাজার। তাই বাড়তি খরচের হিসাব শূন্য দেখায়।',
        'মাসের শেষের মোট টাকা দেখে এই ঝুঁকি বোঝা কঠিন। FinPilot সিদ্ধান্ত নেওয়ার আগেই সেটি দেখায়।'),
    section('স্লাইড ৪ · AI, যাচাই ও ডেমো · ২:১০–৩:০০',
        'অ্যাপ আগে টাকার হিসাব করে, তারপর Groq AI তথ্যগুলো সহজ করে বুঝিয়ে বলে। AI টাকা পাঠাতে বা পেমেন্ট করতে পারে না। AI কাজ না করলে অ্যাপ সেটি জানিয়ে হিসাবভিত্তিক ব্যাখ্যা দেয়।',
        'সিস্টেমটি Python, Django ও PostgreSQL দিয়ে তৈরি। আগে থাকা ছোট ব্যবসার অ্যাপে আমি Personal Mode এবং চারটি ব্যক্তিগত পরিস্থিতি যোগ করেছি। যাচাই করা রিলিজে তিনশ আটষট্টিটি ডেটাবেস টেস্ট পাস করেছে। সাত ধরনের স্ক্রিন সাইজেও ব্রাউজার চেক হয়েছে।',
        'QR কোড স্ক্যান করে কোনো অ্যাকাউন্ট ছাড়াই নমুনা তথ্য দিয়ে ডেমো দেখা যাবে। এই ডেমোর ব্যাখ্যা হিসাবভিত্তিক। প্রাইভেট ওয়ার্কস্পেসে Groq AI ব্যবহার করা যায়।',
        'খরচের আগে নিজের টাকার অবস্থা বুঝে সিদ্ধান্ত নেওয়াই FinPilot-এর মূল লক্ষ্য। ধন্যবাদ।'),
]


def english_guide():
    return [
        section('1. The project in one minute',
            'FinPilot AI is a Financial Survival Copilot. It helps freelancers, students, individual sellers and small business owners understand when they may run short of cash. It combines money records, dated calculations, what-if tests and AI explanations.',
            'A person can expect enough income this month and still miss a bill due tomorrow. FinPilot focuses on that timing problem. It helps users plan before spending; it does not control their bank account.')
        +section('Who built it?', 'Md. Meherab Hossain Talukder — Solo Participant. The buildathon version adds a consumer workflow to an existing small-business application. The whole system was not built from zero during the event.')
        +section('The four-slide presentation', 'Slide 1 introduces the project. Slide 2 explains the solution. Slide 3 proves the timing insight with a simple example. Slide 4 explains AI, validation and demo access. The QR code opens the public synthetic demo.')
        +section('Two separate ways to use it', 'Personal Mode uses personal cash, expected income, bills and a reserve target. Business Mode keeps the existing tools for cash planning, important payments, overdue customer collections and reports. One account can keep these workspaces separate.'),
        section('2. How a user gets value', 'The main workflow is: enter records → understand cash → compare a decision → read the explanation → decide what to do.')
        +bullets('Set up a personal workspace with available cash, expected income and its date, essential bills, and an emergency reserve. An optional savings goal can be added.',
                 'Review the dashboard: paid cash, upcoming bills, cash after bills, the reserve target and a conservative spending estimate.',
                 'Keep records accurate. Received income is different from a payment someone promises to send. Missing expenses can make the estimate incomplete.',
                 'Compare a what-if scenario with the original plan. Saving a scenario keeps a hypothetical comparison; it does not create a real payment.',
                 'Ask the private Advisor about the records and export a PDF, CSV or spreadsheet report for review.')
        +section('The four what-if tests', 'Delay one expected receipt by 7, 14 or 30 days. Add an unexpected expense. Model a proposed savings transfer. Reduce future income by 10, 20 or 30 percent. Each test uses dates and amounts, so the result can change with the chosen timing.')
        +section('What “spending room” means', 'The conservative estimate excludes all future income and checks the lowest dated cash balance against the reserve target. In simple terms: spending room = the larger of zero and [lowest cash without future income minus the reserve]. This is an estimate based on entered records, not a safety guarantee.'),
        section('3. The example you should explain', 'All figures below are synthetic: they are made-up records used to demonstrate the app.')
        +bullets('Paid cash: BDT 18,000.', 'Upcoming essential bills: BDT 12,000.', 'Expected client income: BDT 10,000.', 'Emergency reserve target: BDT 8,000.')
        +section('Original plan', 'If income arrives before the bill, ending cash is 18,000 + 10,000 − 12,000 = BDT 16,000. The reserve is not breached in this example.')
        +section('Payment arrives seven days late', 'Ending cash is still BDT 16,000 after the income finally arrives. But after paying the bill and before receiving income, cash falls to 18,000 − 12,000 = BDT 6,000. The reserve gap is 8,000 − 6,000 = BDT 2,000.',
            'This is a reserve shortfall, not negative cash. The important message is: the same ending balance can hide a very different week. The user can see the risk and review their choices before spending.')
        +section('Why spending room is zero', 'Without counting future income, only BDT 6,000 remains after bills. This is below the BDT 8,000 reserve, so the conservative spending estimate is zero. The app does not treat an unpaid promise as available cash.'),
        section('4. AI, technology and important limits', 'Python and Django run the application. PostgreSQL stores the records. Decimal arithmetic calculates money figures. Groq helps explain authorized evidence, while structured checks validate the model response. The interface uses templates, responsive CSS and JavaScript.')
        +section('What AI does and does not do', 'The calculation engine provides the numbers and dates. AI helps explain relevant information, assumptions and possible choices. It cannot move money, execute payments or approve a loan. If the provider fails or its output is invalid, the app gives a clearly labeled calculation-based explanation.')
        +section('Public demo versus private AI', 'The public demo needs no account, uses made-up data and gives deterministic, calculation-based explanations. It does not make a paid Groq request. Private workspaces can use the configured Groq Advisor. The saved AI image in the earlier materials shows a verified response from a synthetic private workspace.')
        +section('What has been checked', 'At the documented release, 368 PostgreSQL tests passed. Browser checks covered seven screen widths, from phones to desktop screens. These checks support software reliability; they do not prove that financial projections are always correct.')
        +section('Current limits and next steps', 'Results depend on complete, correct records and assumptions about payment timing. Bank synchronization, automatic notifications and autonomous payments are not claimed features. Future work includes consent-based bank imports and richer personal budgeting. The app is decision support, not a promise of profit or financial safety.')
        +section('Try it', 'Scan the QR code in slide 4, or visit https://finpilot-ai-web.onrender.com/demo/personal/ . Source: https://github.com/meherabmehu/finpilot-ai-sme-copilot .'),
    ]


def bengali_guide():
    return [
        section('১. এক মিনিটে প্রজেক্টটি বুঝুন',
            'FinPilot AI হলো টাকা নিয়ে সিদ্ধান্ত নেওয়ার সহকারী অ্যাপ। ফ্রিল্যান্সার, শিক্ষার্থী, ছোট বিক্রেতা ও ছোট ব্যবসার মালিক কখন হাতে টাকার ঘাটতিতে পড়তে পারেন, তা বুঝতে এটি সাহায্য করে। অ্যাপে তথ্য রাখা যায়, তারিখ ধরে হিসাব করা যায়, কোনো সিদ্ধান্ত নিলে কী হতে পারে তা দেখা যায় এবং AI দিয়ে ব্যাখ্যা পাওয়া যায়।',
            'মাসে মোট আয় ভালো হলেও আগামীকাল বিল দেওয়ার সময় টাকা নাও থাকতে পারে। কারণ আয় আসার তারিখ এবং বিল দেওয়ার তারিখ এক নয়। FinPilot এই সময়ের ফারাকটি দেখায়। এটি ব্যাংক অ্যাকাউন্ট নিয়ন্ত্রণ করে না।')
        +section('কে তৈরি করেছেন?', 'Md. Meherab Hossain Talukder — Solo Participant। আগে ছোট ব্যবসার জন্য তৈরি একটি অ্যাপের ওপর এই প্রতিযোগিতার জন্য ব্যক্তিগত অর্থ ব্যবস্থাপনার অংশ যোগ করা হয়েছে। পুরো অ্যাপ প্রতিযোগিতার সময় শূন্য থেকে তৈরি করা হয়েছে—এমন দাবি নেই।')
        +section('চার স্লাইডের গল্প', 'প্রথম স্লাইডে পরিচয়, দ্বিতীয়টিতে সমাধান, তৃতীয়টিতে টাকার সময়ভিত্তিক উদাহরণ, চতুর্থটিতে AI, যাচাই এবং ডেমোর QR কোড। উপস্থাপনায় সমাধান ও উদাহরণে বেশি সময় দিন।')
        +section('দুটি আলাদা ব্যবহার', 'Personal Mode ব্যক্তিগত টাকা, সম্ভাব্য আয়, বিল ও জরুরি তহবিলের জন্য। Business Mode ব্যবসার টাকা, গুরুত্বপূর্ণ পেমেন্ট, বকেয়া পাওনা ও রিপোর্টের জন্য। একই অ্যাকাউন্টে ব্যক্তিগত এবং ব্যবসার তথ্য আলাদা ওয়ার্কস্পেসে রাখা যায়।'),
        section('২. ব্যবহারকারী কীভাবে সুবিধা পাবেন?', 'মূল ধাপ হলো: তথ্য দিন → টাকার অবস্থা বুঝুন → সিদ্ধান্ত পরীক্ষা করুন → ব্যাখ্যা পড়ুন → নিজে সিদ্ধান্ত নিন।')
        +bullets('Personal workspace খুলে হাতে থাকা টাকা, সম্ভাব্য আয় ও তারিখ, জরুরি বিল এবং জরুরি তহবিলের লক্ষ্য দিন। চাইলে সঞ্চয়ের লক্ষ্যও দিন।',
                 'ড্যাশবোর্ডে দেখুন: পাওয়া টাকা, সামনে থাকা বিল, বিলের পর বাকি টাকা, জরুরি তহবিল এবং বাড়তি খরচের হিসাব।',
                 'তথ্য ঠিক রাখুন। টাকা পাওয়া আর কেউ ভবিষ্যতে টাকা দেওয়ার কথা বলা এক নয়। কোনো খরচ বাদ পড়লে হিসাব অসম্পূর্ণ হবে।',
                 'কোনো সিদ্ধান্ত নেওয়ার আগে নতুন পরিস্থিতির সঙ্গে আগের পরিকল্পনা তুলনা করুন। Scenario save করা মানে নমুনা পরিকল্পনা রাখা; আসল টাকা পাঠানো নয়।',
                 'প্রাইভেট Advisor-এ প্রশ্ন করুন। পর্যালোচনার জন্য PDF, CSV বা Excel ধরনের রিপোর্ট নামান।')
        +section('চার ধরনের পরিস্থিতি পরীক্ষা', 'একটি সম্ভাব্য আয় ৭, ১৪ বা ৩০ দিন দেরি হলে কী হয়; হঠাৎ খরচ বাড়লে কী হয়; সঞ্চয়ে টাকা সরালে কী হয়; ভবিষ্যৎ আয় ১০, ২০ বা ৩০ শতাংশ কমলে কী হয়। পরিমাণ ও তারিখ বদলালে ফলও বদলাতে পারে।')
        +section('বাড়তি খরচের হিসাব কী?', 'এখানে ভবিষ্যতে আসতে পারে এমন টাকা ধরা হয় না। সম্ভাব্য সবচেয়ে কম নগদ টাকার সঙ্গে জরুরি তহবিলের লক্ষ্য তুলনা করা হয়। তহবিলের জন্য টাকা রেখে বাড়তি কিছু না থাকলে খরচের হিসাব শূন্য। এটি দেওয়া তথ্যের ওপর নির্ভরশীল অনুমান, নিরাপত্তার নিশ্চয়তা নয়।'),
        section('৩. উদাহরণটি পরিষ্কারভাবে বুঝুন', 'নিচের সব তথ্য শুধু অ্যাপ বোঝানোর জন্য তৈরি। এগুলো কোনো প্রকৃত গ্রাহকের তথ্য নয়।')
        +bullets('হাতে পাওয়া টাকা: ১৮,০০০ টাকা।', 'সামনে জরুরি বিল: ১২,০০০ টাকা।', 'ক্লায়েন্টের কাছ থেকে আসতে পারে: ১০,০০০ টাকা।', 'জরুরি তহবিলে রাখতে চাই: ৮,০০০ টাকা।')
        +section('টাকা সময়মতো এলে', 'বিলের আগে ক্লায়েন্ট টাকা দিলে শেষে থাকে: ১৮,০০০ + ১০,০০০ − ১২,০০০ = ১৬,০০০ টাকা। এই উদাহরণে জরুরি তহবিলের লক্ষ্য ভাঙে না।')
        +section('টাকা সাত দিন দেরিতে এলে', 'ক্লায়েন্ট শেষ পর্যন্ত টাকা দেওয়ার পরেও থাকে ১৬,০০০ টাকা। কিন্তু বিল দেওয়ার পর এবং আয় আসার আগে হাতে থাকে: ১৮,০০০ − ১২,০০০ = ৬,০০০ টাকা। জরুরি তহবিলের ঘাটতি হয়: ৮,০০০ − ৬,০০০ = ২,০০০ টাকা।',
            'এর মানে ব্যালেন্স ঋণাত্মক হয়নি। বরং জরুরি অবস্থার জন্য রাখতে চাওয়া টাকার চেয়ে কম টাকা আছে। মাসের শেষে একই টাকা থাকলেও মাঝখানে ঝুঁকি তৈরি হয়। FinPilot এই ঝুঁকি আগে বুঝতে সাহায্য করে।')
        +section('বাড়তি খরচের হিসাব শূন্য কেন?', 'ভবিষ্যৎ আয় বাদ দিয়ে বিলের পর থাকে ৬,০০০ টাকা। অথচ জরুরি তহবিলের লক্ষ্য ৮,০০০। তাই বাড়তি খরচের সুযোগ দেখায় না। এখনো না পাওয়া টাকাকে হাতে থাকা টাকা ধরে খরচ করতে বলে না।'),
        section('৪. AI, প্রযুক্তি এবং সীমাবদ্ধতা', 'Python ও Django দিয়ে অ্যাপ চলে। PostgreSQL-এ তথ্য রাখা হয়। Decimal পদ্ধতিতে টাকার হিসাব করা হয়। Groq AI অনুমোদিত তথ্যের ব্যাখ্যা দিতে সাহায্য করে। AI-এর উত্তর গঠন ও তথ্যসূত্রের নিয়ম মেনে এসেছে কি না, সেটি যাচাই করা হয়।')
        +section('AI কী করে, কী করে না?', 'হিসাবের অংশ আগে টাকার পরিমাণ ও তারিখ বের করে। তারপর AI প্রাসঙ্গিক তথ্য, অনুমান ও সম্ভাব্য করণীয় বুঝিয়ে বলে। AI টাকা পাঠাতে, পেমেন্ট করতে বা ঋণ অনুমোদন করতে পারে না। AI সেবা না চললে বা উত্তর নিয়ম না মানলে অ্যাপ স্পষ্টভাবে হিসাবভিত্তিক ব্যাখ্যা দেখায়।')
        +section('Public demo আর private AI এক নয়', 'Public demo-তে অ্যাকাউন্ট লাগে না। এতে তৈরি করা নমুনা তথ্য ও নিয়মভিত্তিক ব্যাখ্যা ব্যবহার হয়; paid Groq request হয় না। প্রাইভেট ওয়ার্কস্পেসে সেট করা Groq Advisor ব্যবহার করা যায়। আগের presentation materials-এর saved AI ছবিটি নমুনা private workspace-এ পাওয়া যাচাই করা উত্তর।')
        +section('কী কী যাচাই করা হয়েছে?', 'নথিভুক্ত রিলিজে PostgreSQL-এর ৩৬৮টি টেস্ট পাস করেছে। মোবাইল থেকে desktop পর্যন্ত সাতটি screen width-এ browser check হয়েছে। এগুলো সফটওয়্যার যাচাই; ভবিষ্যতের সব আর্থিক অনুমান ঠিক হবে—এমন প্রমাণ নয়।')
        +section('সীমাবদ্ধতা ও পরবর্তী পরিকল্পনা', 'ভুল বা অসম্পূর্ণ তথ্য দিলে ফলও ভুল হতে পারে। ব্যাংকের তথ্য নিজে থেকে আনা, স্বয়ংক্রিয় notification বা নিজে টাকা পাঠানো এখন চালু আছে—এমন দাবি নেই। ভবিষ্যতে সম্মতি নিয়ে bank import ও আরও ভালো personal budget যোগ করার পরিকল্পনা আছে।')
        +section('ডেমো দেখবেন কীভাবে?', 'Presentation-এর চতুর্থ স্লাইডের QR স্ক্যান করুন। অথবা খুলুন: https://finpilot-ai-web.onrender.com/demo/personal/ । কোড: https://github.com/meherabmehu/finpilot-ai-sme-copilot ।'),
    ]


def render_document(page, filename, title, language, contents, speech=False):
    subtitle = ('চার স্লাইডের জন্য সহজ ভাষার বক্তব্য · লক্ষ্য প্রায় ৩ মিনিট। সময় ধরে অনুশীলন করুন।'
                if language == 'bn' else 'Simple speech for four slides · target about 3 minutes. Rehearse with a timer.') if speech else (
                'সহজ ভাষায় প্রজেক্টের কাজ, ব্যবহার, উদাহরণ ও সীমাবদ্ধতা।' if language == 'bn' else 'A plain-language guide to the project, workflow, example and limits.')
    sheets = []
    for index, body in enumerate(contents, 1):
        heading = title if index == 1 else ('FinPilot AI · '+('বক্তব্য' if speech else 'প্রজেক্ট ব্যাখ্যা') if language == 'bn' else 'FinPilot AI · '+('Presentation speech' if speech else 'Project explanation'))
        sheets.append(f'<section class="sheet"><header><div class="brand">FINPILOT AI</div><h1>{html.escape(heading)}</h1><div class="subtitle">{html.escape(subtitle)}</div><div class="byline">Md. Meherab Hossain Talukder · Solo Participant</div></header><main>{body}</main><footer><span>{"বাংলা" if language == "bn" else "English"} · {"Speech" if speech else "Project guide"}</span><span>{index} / {len(contents)}</span></footer></section>')
    font = Path('C:/Windows/Fonts/Nirmala.ttc').as_uri()
    markup = f'''<!doctype html><html lang="{language}"><head><meta charset="utf-8"><style>
    @font-face{{font-family:NirmalaLocal;src:url('{font}')}}*{{box-sizing:border-box}}@page{{size:A4;margin:0}}body{{margin:0;color:#182f43;font-family:{'NirmalaLocal, ' if language == 'bn' else ''}Arial,sans-serif;background:white}}.sheet{{width:210mm;height:297mm;padding:15mm 16mm 17mm;position:relative;break-after:page;overflow:hidden}}.sheet:last-child{{break-after:auto}}.brand{{font:bold 10pt Arial;letter-spacing:2px;color:#087f73}}h1{{font-size:21pt;line-height:1.35;margin:4mm 0 2mm}}.subtitle{{font-size:10pt;color:#526174;line-height:1.6}}.byline{{font:9pt Arial;color:#526174;margin:3mm 0 5mm;padding-bottom:4mm;border-bottom:1px solid #d4e4e2}}h2{{font-size:13pt;line-height:1.5;color:#087f73;margin:4mm 0 2mm;break-after:avoid}}p,li{{font-size:{'11' if language=='bn' else '10.7'}pt;line-height:{'1.8' if language=='bn' else '1.65'};margin:0 0 2.6mm;overflow-wrap:anywhere}}ul{{padding-left:5mm;margin:2mm 0 4mm}}li{{margin-bottom:2mm}}footer{{position:absolute;left:16mm;right:16mm;bottom:8mm;border-top:1px solid #d4e4e2;padding-top:3mm;display:flex;justify-content:space-between;font:9pt Arial;color:#526174}}main{{max-height:235mm}}
    </style></head><body>{''.join(sheets)}</body></html>'''
    source = PREVIEW/(filename+'.html')
    source.write_text(markup, encoding='utf-8')
    page.goto(source.as_uri())
    page.evaluate('document.fonts.ready')
    checks = page.locator('.sheet').evaluate_all('(items)=>items.map((s,i)=>{const m=s.querySelector("main"),f=s.querySelector("footer");return {page:i+1,bottom:m.getBoundingClientRect().bottom,footer:f.getBoundingClientRect().top,overflow:s.scrollHeight>s.clientHeight+1}})')
    assert all(not item['overflow'] and item['bottom'] < item['footer']-8 for item in checks), (filename, checks)
    destination = OUT/(filename+'.pdf')
    page.pdf(path=str(destination),print_background=True,prefer_css_page_size=True)
    pdf = PdfReader(destination)
    assert len(pdf.pages) == len(contents)
    for index, sheet in enumerate(page.locator('.sheet').all(), 1):
        sheet.screenshot(path=str(PREVIEW/f'{filename}-{index}.png'))
    print(f'{filename}.pdf: {len(pdf.pages)} pages; layout check passed.',flush=True)
    return {'file':destination.name,'pages':len(pdf.pages),'language':language,'type':'speech' if speech else 'explanation','bytes':destination.stat().st_size}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    PREVIEW.mkdir(parents=True,exist_ok=True)
    reports = []
    with sync_playwright() as pw:
        installed = sorted((Path.home()/'AppData/Local/ms-playwright').glob('chromium-*/chrome-win64/chrome.exe'))
        browser = pw.chromium.launch(executable_path=str(installed[-1])) if installed else pw.chromium.launch(channel='chromium')
        page = browser.new_page(viewport={'width':794,'height':1123},device_scale_factor=1.5)
        reports.append(render_document(page,'FinPilot_Speech_English','3-minute presentation speech','en',[SPEECH_EN[0]+SPEECH_EN[1],SPEECH_EN[2]+SPEECH_EN[3]],True))
        reports.append(render_document(page,'FinPilot_Speech_Bangla','তিন মিনিটের উপস্থাপনার বক্তব্য','bn',[SPEECH_BN[0]+SPEECH_BN[1],SPEECH_BN[2]+SPEECH_BN[3]],True))
        reports.append(render_document(page,'FinPilot_Project_Explanation_English','The complete project, explained simply','en',english_guide()))
        reports.append(render_document(page,'FinPilot_Project_Explanation_Bangla','সহজ ভাষায় পুরো প্রজেক্টের ব্যাখ্যা','bn',bengali_guide()))
        browser.close()
    assert len(reports) == 4
    (PREVIEW/'verification.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
