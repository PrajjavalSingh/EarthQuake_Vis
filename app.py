from flask import Flask, request, render_template
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/earthquake_data_gatherer', methods=['POST'])
def earthquake_data_gatherer():
    arg1 = request.form['start_date']
    arg2 = request.form['end_date']
    arg3 = request.form['min_mag']
    arg4 = request.form['max_mag']
    command = [ 'python', 'earthquake_Reader_Presenter.py', arg1, arg2, arg3, arg4 ]
    try:
        result = subprocess.run( command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True )
        return result
    except subprocess.CalledProcessError as e:
        print( "Subprocess error : ", e )
        return

if  __name__ == '__main__':
    app.run()