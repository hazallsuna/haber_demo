from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/Monster/Desktop/optimum-sound-451409-g0-a0cdc23028f4.json"

app = Flask(__name__)

def get_haberler():
    url = "https://www.sozcu.com.tr/"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Hata oluştu:", e)
        return ["Haberler çekilemedi."]
    
    soup = BeautifulSoup(response.text, "html.parser")
    container = soup.find("div", class_="col-lg-12 mb-0 mb-lg-4 surmanset order-3 order-lg-1")

    haber_listesi = []
    if container:
        a_etiketleri = container.find_all("a")
        for a in a_etiketleri:  
            baslik = a.get_text(strip=True)
            if baslik:
                haber_listesi.append(baslik)
    else:
        haber_listesi.append("İlgili bölüm bulunamadı.")
    
    return haber_listesi

def generate_magazine_news(haber_listesi):
    client = genai.Client(
        vertexai=True,
        project="optimum-sound-451409-g0", 
        location="us-central1",
    )

    magazin_haberleri = []

    for haber_baslik in haber_listesi:
        prompt_text = f"'{haber_baslik}'başlığını Seda Sayan yorumuyla magazinsel bir şekilde 100 kelimelik haber formatında yaz."

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt_text)]
            )
        ]

        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=4096,  
            response_modalities=["TEXT"],
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=contents,
            config=generate_content_config
        )

        if response and response.candidates:
            full_text = response.candidates[0].content.parts[0].text.strip()
            magazin_haberleri.append(full_text)
        else:
            magazin_haberleri.append("Magazin yorumu üretilemedi.")

    return magazin_haberleri  

@app.route("/")
def index():
    haberler = get_haberler()
    llm_output = generate_magazine_news(haberler)
    return render_template("index.html", haberler=haberler, llm_output=llm_output)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
