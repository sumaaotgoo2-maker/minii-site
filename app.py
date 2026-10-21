from flask import Flask, request, render_template_string
import cv2
import numpy as np
import base64
import colorsys
import os

app = Flask(__name__)

HTML_CODE = """
<!DOCTYPE html>
<html lang="mn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Миний Өнгө - Personal Color</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600&display=swap');
        
        body { 
            font-family: 'Montserrat', sans-serif; 
            background-color: #fdfaf6; 
            color: #333; 
            margin: 0; 
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container { 
            background: #ffffff; 
            padding: 40px; 
            border-radius: 20px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.05); 
            max-width: 500px; 
            width: 90%;
            text-align: center;
        }
        h1 { font-weight: 600; color: #5a4b41; margin-bottom: 10px; font-size: 24px;}
        p { font-weight: 300; color: #888; font-size: 14px; margin-bottom: 30px;}
        
        .upload-area {
            border: 2px dashed #d4c4b7;
            padding: 30px;
            border-radius: 15px;
            background-color: #faf7f2;
            margin-bottom: 20px;
            cursor: pointer;
            transition: 0.3s;
        }
        .upload-area:hover { background-color: #f5efe6; }
        input[type="file"] { display: none; }
        .upload-btn {
            background-color: #5a4b41; 
            color: white; 
            padding: 12px 30px; 
            border: none; 
            border-radius: 25px; 
            cursor: pointer; 
            font-size: 14px;
            font-weight: 400;
            transition: 0.3s;
        }
        .upload-btn:hover { background-color: #3e332c; }
        
        .result-box { margin-top: 30px; text-align: left; background: #faf7f2; padding: 20px; border-radius: 15px; }
        .result-title { font-size: 20px; font-weight: 600; color: #5a4b41; margin-bottom: 10px; border-bottom: 1px solid #e0d6cc; padding-bottom: 10px;}
        .result-text { font-size: 15px; line-height: 1.6; margin-bottom: 15px;}
        
        img { max-width: 100%; border-radius: 15px; margin-top: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);}
    </style>
</head>
<body>
    <div class="container">
        <h1>Өөрийн Өнгийг Нээ</h1>
        <p>Гэрэлтэй, нүүр будалтгүй зургаа оруулаад, танд тохирох өнгөний ертөнцийг мэдээрэй.</p>
        
        <form method="POST" enctype="multipart/form-data">
            <label for="file-upload" class="upload-area">
                <div style="font-size: 30px; color: #d4c4b7; margin-bottom: 10px;">📸</div>
                <div style="color: #888; font-size: 14px;">Зураг оруулахыг хүсвэл энд дарна уу</div>
                <input id="file-upload" type="file" name="file" accept="image/*" required onchange="this.form.submit()">
            </label>
        </form>

        {% if result %}
            <div class="result-box">
                <div class="result-title">Таны үр дүн:</div>
                <div class="result-text">
                    {{ result|safe }}
                </div>
                <img src="data:image/jpeg;base64,{{ image_data }}" />
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            img_bytes = file.read()
            npimg = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            result_text = "Нүүр олдсонгүй! Өөр зураг оруулна уу."
            if len(faces) > 0:
                for (x, y, w, h) in faces:
                    roi = img_rgb[y + int(h/2):y + h, x + int(w/4):x + int(3*w/4)]
                    avg_color = np.mean(roi, axis=(0, 1)).astype(int)
                    
                    r, g, b = [val / 255.0 for val in avg_color]
                    h_val, l_val, s_val = colorsys.rgb_to_hls(r, g, b)
                    h_deg = h_val * 360
                    
                    if (h_deg >= 0 and h_deg <= 50) or (h_deg >= 330 and h_deg <= 360):
                        undertone = "Дулаан (Warm)"
                    else:
                        undertone = "Хүйтэн (Cool)"
                        
                    if l_val > 0.6: depth = "Цайвар"
                    elif l_val < 0.3: depth = "Бараан"
                    else: depth = "Дунд"
                        
                    if "Дулаан" in undertone:
                        if depth == "Цайвар": season = "Хавар 🌸"
                        elif depth == "Бараан": season = "Намар 🍁"
                        else: season = "Дулаан (Намар/Хавар)"
                    else:
                        if depth == "Цайвар": season = "Зун ☀️"
                        elif depth == "Бараан": season = "Өвөл ❄️"
                        else: season = "Хүйтэн (Зун/Өвөл)"

                    rgb_clean = f"{avg_color[0]}, {avg_color[1]}, {avg_color[2]}"
                    result_text = f"Арьсны өнгө: {undertone}<br>Гэрэлтэлт: {depth}<br>Улирлын төрөл: <b>{season}</b><br>(RGB: {rgb_clean})"
                    
                    _, buffer = cv2.imencode('.jpg', img)
                    image_data = base64.b64encode(buffer).decode('utf-8')
                    return render_template_string(HTML_CODE, result=result_text, image_data=image_data)
            
            return render_template_string(HTML_CODE, result=result_text)
    return render_template_string(HTML_CODE)

# Сервер дээр ажиллах хэсэг
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
