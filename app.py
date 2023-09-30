from flask import Flask, request, render_template, jsonify
import subprocess
import earthquake_Reader_Presenter as erp

app = Flask(__name__)

@app.route('/')
def index():
    return render_template( 'index.html' )

@app.route('/earthquake_data_gatherer', methods=['POST'])
def earthquake_data_gatherer():
    startdate = request.form['start_date']
    enddate = request.form['end_date']
    minmag = request.form['min_mag']
    maxmag = request.form['max_mag']
    earthquakedata = erp.DataFetcherAndPresenter(startdate,enddate,minmag,maxmag)
    earthquakedata.fetchdata()
    coordinates, colidxs = earthquakedata.getLatLongCoordinatesAndValidMags()
    fig_html = earthquakedata.displayOnWorldMap( coordinates, colidxs )
    return render_template( 'index.html', plot_html=fig_html )

if  __name__ == '__main__':
    app.run(debug=True)