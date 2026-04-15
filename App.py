from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename
import subprocess
from PIL import Image

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
CONVERTED_FOLDER = 'converted'
ALLOWED_EXTENSIONS = set(['mp3', 'mp4', 'wav', 'avi', 'mov', 'jpg', 'jpeg', 'png', 'gif', 'pdf', 'docx'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_file(input_path, output_path, output_format):
    ext = output_format.lower()
    if ext in ['mp3', 'mp4', 'wav', 'avi', 'mov']:
        # Use ffmpeg for audio/video
        cmd = ['ffmpeg', '-y', '-i', input_path, output_path]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif ext in ['jpg', 'jpeg', 'png', 'gif']:
        # Use Pillow for images
        with Image.open(input_path) as img:
            img.save(output_path)
    else:
        raise ValueError('Unsupported conversion')

# Define allowed conversions: input_ext -> [output_ext1, output_ext2, ...]
ALLOWED_CONVERSIONS = {
    'mp3': ['mp4', 'wav', 'avi', 'mov'],
    'mp4': ['mp3', 'wav', 'avi', 'mov'],
    'wav': ['mp3', 'mp4', 'avi', 'mov'],
    'avi': ['mp3', 'mp4', 'wav', 'mov'],
    'mov': ['mp3', 'mp4', 'wav', 'avi'],
    'jpg': ['jpeg', 'png', 'gif', 'jpg'],
    'jpeg': ['jpg', 'png', 'gif', 'jpeg'],
    'png': ['jpg', 'jpeg', 'gif', 'png'],
    'gif': ['jpg', 'jpeg', 'png', 'gif'],
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(input_path)
            input_ext = filename.rsplit('.', 1)[1].lower()
            output_format = request.form['output_format']
            # Check if this conversion is allowed
            if output_format not in ALLOWED_CONVERSIONS.get(input_ext, []):
                flash(f'Cannot convert {input_ext.upper()} to {output_format.upper()}')
                return redirect(request.url)
            base = os.path.splitext(filename)[0]
            output_filename = f"{base}.{output_format}"
            output_path = os.path.join(app.config['CONVERTED_FOLDER'], output_filename)
            try:
                convert_file(input_path, output_path, output_format)
            except Exception as e:
                flash(f'Conversion failed: {e}')
                return redirect(request.url)
            return redirect(url_for('download_file', filename=output_filename))
        else:
            flash('File type not allowed')
            return redirect(request.url)
    # For GET, determine allowed output formats for the dropdown (default: all if not recognized)
    input_ext = request.args.get('input_ext')
    if input_ext in ALLOWED_CONVERSIONS:
        allowed_outputs = ALLOWED_CONVERSIONS[input_ext]
    else:
        # Show all unique output formats if no file selected or unknown type
        allowed_outputs = sorted(set(fmt for fmts in ALLOWED_CONVERSIONS.values() for fmt in fmts))
    return render_template('index.html', allowed_outputs=allowed_outputs)

@app.route('/converted/<filename>')
def download_file(filename):
    return send_from_directory(app.config['CONVERTED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
