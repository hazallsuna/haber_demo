
from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

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
    prompt_text = "Aşağıdaki haber başlıklarını sanki Seda Sayan yorumluyormuş gibi yaz , her biri 250 kelime olacak şekilde kurgula:\n"
    for idx, baslik in enumerate(haber_listesi, start=1):
        prompt_text += f"{idx}. {baslik}\n"

    client = genai.Client(
        vertexai=True,
        project="optimum-sound-451409-g0", 
        location="us-central1",
    )

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
        full_text = response.candidates[0].content.parts[0].text
        haberler = full_text.strip().split("\n\n")  
        
        return [haber.strip() for haber in haberler if haber.strip()] 

    return ["Modelden bir yanıt alınamadı."]


@app.route("/")
def index():
    haberler = get_haberler()
    llm_output = generate_magazine_news(haberler)
    return render_template("index.html", haberler=haberler, llm_output=llm_output)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
