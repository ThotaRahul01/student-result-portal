from flask import Flask, render_template, request, redirect, session, url_for, send_file, abort
import json, io, os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
app = Flask(__name__)
app.secret_key = 'secret123'
with open('data.json') as f:
    student_data = json.load(f)

def make_pdf(htno, semester):
    sem_key = 'sem1' if semester=='sem1' else 'sem2'
    if htno not in student_data or sem_key not in student_data[htno]:
        return None
    sem = student_data[htno][sem_key]
    subjects = sem['subjects']
    grades = sem['grades']
    sgpa = sem.get('SGPA') if sem.get('SGPA') is not None else 'N/A'
    # compute cgpa
    other = 'sem2' if sem_key=='sem1' else 'sem1'
    cgpa = None
    if other in student_data[htno] and student_data[htno][other].get('SGPA') is not None and sem.get('SGPA') is not None:
        try:
            cgpa = round((float(student_data[htno][other]['SGPA']) + float(sem.get('SGPA')))/2,2)
        except:
            cgpa = None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30,leftMargin=30, topMargin=30,bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()
    logo_path = os.path.join('static','images','logo.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=80, height=80))
    elements.append(Paragraph('<b>GEETHANJALI COLLEGE OF ENGINEERING & TECHNOLOGY</b>', styles['Title']))
    elements.append(Paragraph('<i>...Striving Towards Perfection</i>', styles['Normal']))
    elements.append(Spacer(1,12))
    elements.append(Paragraph(f'<b>Hall Ticket:</b> {htno}    <b>Semester:</b> { "1" if sem_key=="sem1" else "2" }', styles['Normal']))
    elements.append(Spacer(1,12))
    data = [['Subject Code','Subject Name','Grade']]
    for i,(code,name) in enumerate(subjects.items()):
        grade = grades[i] if i < len(grades) else 'N/A'
        data.append([code, name, grade])
    t = Table(data, colWidths=[100,300,80])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(2,0),colors.HexColor('#4CAF50')),('TEXTCOLOR',(0,0),(2,0),colors.whitesmoke),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('BACKGROUND',(0,1),(-1,-1),colors.white)]))
    elements.append(t)
    elements.append(Spacer(1,12))
    elements.append(Paragraph(f'<b>SGPA:</b> {sgpa}', styles['Normal']))
    if cgpa is not None:
        elements.append(Paragraph(f'<b>CGPA:</b> {cgpa}', styles['Normal']))
    status = 'PASS' if all(g not in ['F','Ab','N/A'] for g in grades) else 'FAIL'
    color = 'green' if status=='PASS' else 'red'
    elements.append(Paragraph(f"<b>Status:</b> <font color='{color}'>{status}</font>", styles['Normal']))
    elements.append(Spacer(1,20))
    elements.append(Paragraph('<i>GCET DS Project by Rahul Varma</i>', styles['Normal']))
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET','POST'])
def login():
    if request.method=='POST':
        htno = request.form.get('htno'); pwd = request.form.get('password')
        if htno in student_data and pwd == htno:
            session['htno'] = htno; return redirect('/select')
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/select')
def select():
    if 'htno' not in session: return redirect('/')
    ht = session['htno']
    sem1 = student_data.get(ht,{}).get('sem1'); sem2 = student_data.get(ht,{}).get('sem2')
    sem1_sgpa = sem1.get('SGPA') if sem1 else None; sem2_sgpa = sem2.get('SGPA') if sem2 else None
    cgpa = None
    if sem1_sgpa is not None and sem2_sgpa is not None:
        try:
            cgpa = round((float(sem1_sgpa)+float(sem2_sgpa))/2,2)
        except:
            cgpa = None
    return render_template('select.html', htno=ht, sem1_sgpa=sem1_sgpa, sem2_sgpa=sem2_sgpa, cgpa=cgpa)

@app.route('/result/<semester>')
def result(semester):
    if 'htno' not in session: return redirect('/')
    ht = session['htno']; sem_key = 'sem1' if semester=='sem1' else 'sem2'
    sem = student_data[ht].get(sem_key)
    subjects = sem['subjects']; grades = sem['grades']; sgpa = sem.get('SGPA')
    result_status = 'PASS' if all(g not in ['F','Ab','N/A'] for g in grades) else 'FAIL'
    return render_template('result.html', htno=ht, semester=('1' if sem_key=='sem1' else '2'), subjects=subjects, grades=grades, sgpa=sgpa, cgpa=None if student_data[ht].get('sem1') is None or student_data[ht].get('sem2') is None else round((float(student_data[ht]['sem1'].get('SGPA',0))+float(student_data[ht]['sem2'].get('SGPA',0)))/2,2), result_status=result_status)

@app.route('/download/<semester>')
def download_pdf(semester):
    if 'htno' not in session: return redirect('/')
    ht = session['htno']; buf = make_pdf(ht, semester)
    if buf is None: abort(404)
    fname = f"{ht}_Sem{('1' if semester=='sem1' else '2')}_Result.pdf"
    return send_file(buf, as_attachment=True, download_name=fname, mimetype='application/pdf')

@app.route('/logout')
def logout():
    session.clear(); return redirect('/')

if __name__=='__main__':
    app.run(debug=True)
