import os, sys
sys.path.insert(0, os.path.abspath("."))
import ask

candidates = [
    "llama-3.3-70b-versatile",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "llama-3.1-8b-instant",
    "openai/gpt-oss-20b"
]

prompt_en = "According to Nepal Rastra Bank, what is the maximum ATM fee for IBFT? Answer in one sentence."
prompt_ne = "नेपाल राष्ट्र बैंकको निर्देशन अनुसार एटीएमको सीसीटीभी ब्याकअप कति दिन राख्नुपर्छ? एक वाक्यमा जवाफ दिनुहोस्।"

for model_id in candidates:
    print(f"\n================ Model: {model_id} ================")
    try:
        # Test English
        res_en = ask.client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt_en}],
            max_tokens=60,
            temperature=0.1
        )
        print(" [EN Output]:", res_en.choices[0].message.content.strip().replace('\n', ' '))
        
        # Test Nepali
        res_ne = ask.client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": prompt_ne}],
            max_tokens=60,
            temperature=0.1
        )
        print(" [NE Output]:", res_ne.choices[0].message.content.strip().replace('\n', ' '))
    except Exception as e:
        print(" [ERROR]:", e)

