from flask import Flask, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os

app = Flask(__name__)

def get_font(size):
    # Render (Linux) sistemlerde yaygın bulunan font yolları
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    
    # Eğer yukarıdakiler yoksa varsayılanı yükle (Yine küçük kalabilir ama sistemde font aramış oluruz)
    return ImageFont.load_default()

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        # getbbox ile metnin genişliğini ölçüyoruz
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        
        if width <= max_width - 20: # 20px padding
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    return lines

@app.route('/add-text-to-image', methods=['POST'])
def add_text_to_image():
    try:
        data = request.json
        scene_number = data.get('scene_number', 'unknown')
        dialogues = data.get('dialogues', [])
        bubbles = data.get('bubbles', [])
        image_base64 = data.get('image_base64', '')
        
        # YAZI BOYUTU BURADAN AYARLANIR
        # 1024x1024 bir görsel için 40-50 idealdir.
        FONT_SIZE = 45 
        base_font = get_font(FONT_SIZE)
        
        if not image_base64:
            return jsonify({'error': 'image_base64 gerekli'}), 400
        
        img_bytes = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGBA')
        draw = ImageDraw.Draw(img)
        
        for i, dialogue in enumerate(dialogues):
            if i < len(bubbles):
                bubble = bubbles[i]
            else:
                bubble = {'position': {'x_percent': 10, 'y_percent': 10 + i * 20, 'width_percent': 40, 'height_percent': 20}}
            
            pos = bubble['position']
            x = int(pos['x_percent'] / 100.0 * img.width)
            y = int(pos['y_percent'] / 100.0 * img.height)
            w = int(pos['width_percent'] / 100.0 * img.width)
            h = int(pos['height_percent'] / 100.0 * img.height)
            
            lines = wrap_text(dialogue.strip(), base_font, w)
            
            # Satır yüksekliğini font boyutuna göre dinamik yapalım
            line_height = FONT_SIZE + 5 
            total_text_h = len(lines) * line_height
            start_y = y + (h - total_text_h) // 2
            
            for idx, line in enumerate(lines):
                bbox = base_font.getbbox(line)
                line_w = bbox[2] - bbox[0]
                line_x = x + (w - line_w) // 2
                line_y = start_y + idx * line_height
                
                # Siyah kontur (Görünürlüğü artırmak için)
                for offset in range(2):
                    draw.text((line_x + offset, line_y + offset), line, font=base_font, fill=(0, 0, 0, 255))
                
                # Ana Beyaz Metin
                draw.text((line_x, line_y), line, font=base_font, fill=(255, 255, 255, 255))
        
        output_buffer = io.BytesIO()
        img.save(output_buffer, format='PNG')
        output_b64 = base64.b64encode(output_buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'status': 'success',
            'scene_number': scene_number,
            'filename': f"sahne-{scene_number}-final.png",
            'image_base64': output_b64
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)