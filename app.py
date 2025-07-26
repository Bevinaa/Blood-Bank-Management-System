from flask import Flask,request,render_template,url_for,redirect,session
import cx_Oracle
import random
from datetime import datetime 
import time



app = Flask(__name__)
app.secret_key = 'secret_key'

orcl_connect_str = 'system/orcl7bharath@localhost:1521/XE'

connection = cx_Oracle.connect(orcl_connect_str)
cursor = connection.cursor()

# direct to first page 
@app.route('/')
def index():
    return render_template("trylogin.html")



"""----------------------------------------"""
""" Login Checking"""
"""----------------------------------------"""

@app.route("/form_login",methods=["POST","GET"])
def form_login():


    if request.method == 'POST':
        entered_username = request.form['user']
        entered_password = request.form['pwd']
        entered_role = request.form['role']
        session['email'] = entered_username

        try:
            connection = cx_Oracle.connect(orcl_connect_str)
            cursor = connection.cursor()
            
            # creating the oracle query based on the role user want to login
            if entered_role == "doner":
                query = "SELECT password FROM doner WHERE email = :username"
            elif entered_role == "patient":
                query = "SELECT password FROM patient WHERE email = :username"
            elif entered_role == "bloodbank":
                query = "SELECT password FROM bloodbank WHERE email = :username"

            cursor.execute(query, {'username': entered_username})
            result = cursor.fetchone()

            cursor.close()

            if result:
                db_password = result[0]

                # doner login
                if db_password == entered_password and entered_role == "doner":

                    cursor2 = connection.cursor()
                    query2 = f"select distinct blood_grp from patient"
                    cursor2.execute(query2)
                    bloodgrp = cursor2.fetchall()
                    cursor2.close()

                    cursor3 = connection.cursor()
                    query3 = f"select distinct name from bloodbank"
                    cursor3.execute(query3)
                    bb_names_tup = cursor3.fetchall()
                    bb_name_lst = [i[0] for i in bb_names_tup]
                    cursor3.close()

                    return render_template('donerdonationpage.html',bloodgroups=bloodgrp,input_list=bb_name_lst)

                # blood bank login
                elif db_password == entered_password and entered_role == "bloodbank":


                    #obtaining current session bloodbank id
                    cursor_current = connection.cursor()
                    query_current = f"select id from bloodbank where email = '{session.get('email')}'"
                    cursor_current.execute(query_current)
                    current_session_bloodbank_id = (cursor_current.fetchone())[0]
                    cursor_current.close()


                    cursor3 = connection.cursor()
                    query3 = f"select id,name,gender,age,blood_grp,contact_number,last_donation_date from doner"
                    cursor3.execute(query3)
                    all_dnrs = cursor3.fetchall()
                    cursor3.close()

                    cursor4 = connection.cursor()
                    query4 = f"select id,name,gender,age,blood_grp,contact_number from patient"
                    cursor4.execute(query4)
                    all_pts = cursor4.fetchall()
                    cursor4.close()

                    cursor5 = connection.cursor()
                    query5 = f"select id,name,director,operating_hrs,contact_number,email from bloodbank"
                    cursor5.execute(query5)
                    all_bb = cursor5.fetchall()
                    cursor5.close()

                    cursor6 = connection.cursor()
                    query6 = f"select bb_id,bb_name,d_id,d_name,d_bloodgrp,d_date from available_bloods"
                    cursor6.execute(query6)
                    all_avail_bloods = cursor6.fetchall()
                    cursor6.close()

                    cursor7 = connection.cursor()
                    query7 = f"select bb_id,bb_name,d_id,pt_id,bloodgrp,claim_date from blood_transfer_history where bb_id = '{current_session_bloodbank_id}'"
                    cursor7.execute(query7)
                    bb_history = cursor7.fetchall()
                    cursor7.close()


                    
                    return render_template('bloodbankforum.html',all_doners = all_dnrs,all_patients = all_pts,all_bb = all_bb,all_donations = all_avail_bloods,all_historys = bb_history)

                # patient login
                elif db_password == entered_password and entered_role == "patient":


                    cursor5 = connection.cursor()
                    query5 = f"select id,name,director,operating_hrs,contact_number,email from bloodbank"
                    cursor5.execute(query5)
                    all_bb = cursor5.fetchall()
                    cursor5.close()
                    return render_template('patient_page.html',all_bb = all_bb)


                    return render_template('regdecision.html') 
                else:
                    return render_template('trylogin.html',info="..Wrong Password..")
                    
            else:
                return render_template('trylogin.html',info="..Invalid username..")

                
                  
            
        except cx_Oracle.DatabaseError as e:
            error_message = f"Database Error: {e}"
            return error_message  
        
        finally:
            
            
            connection.close()


    
    

# interface after log page to select registration role
@app.route("/register",methods=["POST","GET"])
def reg():
    return render_template("regdecision.html")


@app.route("/donerpagedirect",methods=["POST","GET"])
def doner_reg():
    return render_template("doner.html")

@app.route("/patientpagedirect",methods=["POST","GET"])
def patient_reg():
    return render_template("patient.html")

@app.route("/bloodbankpagedirect",methods=["POST","GET"])
def bloodbank_reg():
    return render_template("bloodbank.html")





"""------------------------------------------------"""
""" Doner registration  operation"""
""" -----------------------------------------------"""

@app.route("/donerregsubmit", methods=["POST"])
def doner_reg_submit():
    # Previous code remains unchanged

    inp_name = request.form['d_name']
    inp_gender = request.form['d_gender']
    html_dob = request.form['d_dob']
    inp_dob = datetime.strptime(html_dob, '%Y-%m-%d').date()  # Parse and format date
    
    inp_blood_grp = request.form['d_bloodgrp']
    inp_contact = request.form['d_contact']
    inp_med_rep = request.form['d_medicalreport']
    inp_email = request.form['d_email']
    inp_new_pass = request.form['d_pass1']
    inp_re_pass = request.form['d_pass2']
    inp_age = (datetime.now().year) -  inp_dob.year


    # age constraint checking
    if inp_age < 18:

        info = "...Above 18 Years old are eligible to register as Doner"
        return render_template('doner.html',info=info)

    # checking the password 
    elif inp_new_pass != inp_re_pass:

        info = "...please Correct the re-entered password...."
        return render_template('doner.html',info=info)


    """ unique id auto generate """

    timestamp = str(int(time.time() * 1000))  # Using milliseconds for uniqueness
    inp_id = f"D_{timestamp}"
      

    try:
        # Establish Oracle DB connection
        connection = cx_Oracle.connect(orcl_connect_str)

        if request.form['donersubmitbutton'] == "Submit":
            query = f"INSERT INTO doner(id,name,gender,dob,blood_grp,contact_number,med_rpt,email,password,age) VALUES (:id, :name, :gender, :dob, :blood_grp, :contact, :med_rep, :email, :new_pass,:age)"
            cursor = connection.cursor()
            
            # Executing the query with parameters
            cursor.execute(query, {
                'id': inp_id,
                'name': inp_name,
                'gender': inp_gender,
                'dob': inp_dob,
                'blood_grp': inp_blood_grp,
                'contact': inp_contact,
                'med_rep': inp_med_rep,
                'email': inp_email,
                'new_pass': inp_new_pass,
                'age' : inp_age,
                
            })
            
            connection.commit()
            cursor.close()
            connection.close()
            return render_template("info_page.html",common_info = "You have successfully registered go back and login")

    except cx_Oracle.DatabaseError as e:
        error_message = f"Error inserting data: {e}"
        return error_message

    return "Something went wrong"


""" -----------------------------------------------"""
""" patient registration submission operation  """
""" -----------------------------------------------"""



@app.route("/patientregsubmit", methods=["POST"])
def patinet_reg_submit():
    

    inp_name = request.form['pt_name']
    inp_gender = request.form['pt_gender']
    html_dob = request.form['pt_dob']
    inp_dob = datetime.strptime(html_dob, '%Y-%m-%d').date()  # Parse and format date
    
    inp_blood_grp = request.form['ptbloodgrp']
    inp_contact = request.form['pt_contact']
    inp_med_rep = request.form['pt_medical_report']
    inp_email = request.form['pt_email']
    inp_new_pass = request.form['pt_pass1']
    inp_re_pass = request.form['pt_pass2']
    inp_age = (datetime.now().year) -  inp_dob.year

    # checking the password 
    if inp_new_pass != inp_re_pass:

        info = "...please Correct the re-entered password...."
        return render_template('patient.html',info=info)

    """ unique id auto generate """

    timestamp = str(int(time.time() * 1000))  # Using milliseconds for uniqueness
    inp_id = f"PT_{timestamp}" 

    try:
        # Establish Oracle DB connection
        connection = cx_Oracle.connect(orcl_connect_str)

        if request.form['pt_reg_submit'] == "Submit":
            query = f"INSERT INTO patient(id,name,gender,dob,blood_grp,contact_number,med_rpt,email,password,age) VALUES (:id, :name, :gender, :dob, :blood_grp, :contact, :med_rep, :email, :new_pass,:age)"
            cursor = connection.cursor()
            
            # Executing the query with parameters
            cursor.execute(query, {
                'id': inp_id,
                'name': inp_name,
                'gender': inp_gender,
                'dob': inp_dob,
                'blood_grp': inp_blood_grp,
                'contact': inp_contact,
                'med_rep': inp_med_rep,
                'email': inp_email,
                'new_pass': inp_new_pass,
                'age' : inp_age
            })
            
            connection.commit()
            cursor.close()
            connection.close()
            # return render_template("regdecision.html")
            return render_template("info_page.html",common_info = "You have successfully registered go back and login")

    except cx_Oracle.DatabaseError as e:
        error_message = f"Error inserting data: {e}"
        return error_message

    return "Something went wrong"




""" -----------------------------------------------"""
""" blood bank registration submission """
""" -----------------------------------------------"""

@app.route("/bloodbankreg", methods=["POST"])
def bloodbank_reg_submit():
    inp_name = request.form['bb_name']
    inp_dir_name = request.form['bb_director_name']
    inp_add = request.form['bb_address']
    open_t = request.form['open_time']
    close_t = request.form['close_time']
    operating_hrs = open_t + " to " + close_t
    inp_contact = request.form['bb_contact']
    inp_email = request.form['bb_email']
    inp_new_pass = request.form['bb_pass1']
    inp_re_pass = request.form['bb_pass2']

    # checking the password 
    if inp_new_pass != inp_re_pass:

        info = "...please Correct the re-entered password...."
        return render_template('bloodbank.html',info=info)
    
    """ unique id auto generate """

    timestamp = str(int(time.time() * 1000))  # Using milliseconds for uniqueness
    inp_id = f"BB_{timestamp}"

    try:
        # Establishing an Oracle connection 
        connection = cx_Oracle.connect(orcl_connect_str)

        if request.form['bb_submit_button'] == "Submit":
            query = f"INSERT INTO bloodbank VALUES (:b_id, :b_name, :b_dir, :b_add, :b_oper, :b_cont, :b_email, :b_pass)"
            cursor = connection.cursor()

            # Executing the query with the parameter dictionary
            cursor.execute(query, {
                'b_id': inp_id,
                'b_name': inp_name,
                'b_dir': inp_dir_name,
                'b_add': inp_add,
                'b_oper' : operating_hrs,
                'b_cont': inp_contact,
                'b_email': inp_email,
                'b_pass': inp_new_pass
            })

            connection.commit()
            cursor.close()
            connection.close()
            # return render_template("regdecision.html")
            return render_template("info_page.html",common_info = "You have successfully registered go back and login")
        
    except cx_Oracle.DatabaseError as e:
        error_message = f"Error inserting data: {e}"
        return error_message

    return "Something went wrong"



"""--------------------------------------------------"""
"""  doner account removing """
"""--------------------------------------------------"""

@app.route('/smt_rmv_doner',methods = ["POST"])
def rmv_dnr_input():


    connection = cx_Oracle.connect(orcl_connect_str)
    try:
        
        rmv_username = request.form['rmv_mail']
        rmv_pass = request.form['rmv_pass']
        
        csr = connection.cursor()
        query = "select password from doner where email = :d_mail"
        csr.execute(query,{'d_mail':rmv_username})
        rslt = csr.fetchall()
        csr.close()

        if rslt and rslt == rmv_pass:

            rmv_csr = connection.cursor()
            rmv_query = "delete from doner where email = :d_mail"
            rmv_csr.execute(rmv_query,{'d_mail' : rmv_username})
            rmv_csr.close()
            return render_template("info_page.html",common_info="Your acoount has been successfully removed")
                        
                            
        elif rslt is not None:

            cursor2 = connection.cursor()

            query2 = f"select distinct blood_grp from patient"
            cursor2.execute(query2)
            bloodgrp = cursor2.fetchall()
            cursor2.close()
            return render_template('donerdonationpage.html',bloodgroups=bloodgrp,info="..Invalid username or password try again..")
        else:

            cursor2 = connection.cursor()

            query2 = f"select distinct blood_grp from patient"
            cursor2.execute(query2)
            bloodgrp = cursor2.fetchall()
            cursor2.close()
            return render_template('donerdonationpage.html',bloodgroups=bloodgrp,info="..Invalid username or password try again..")

    except cx_Oracle.DatabaseError as e:
        error_message = f"Database Error: {e}"
        return error_message  
                
    finally:
        connection.close()


"""--------------------------------------------------"""
"""  bloodbank account removing """
"""--------------------------------------------------"""

@app.route('/smt_rmv_bloodbank',methods = ["POST"])
def rmv_bloodbank_input():


    connection = cx_Oracle.connect(orcl_connect_str)
    try:
        
        rmv_username = request.form['rmv_mail']
        rmv_pass = request.form['rmv_pass']
        
        csr = connection.cursor()
        query = "select password from bloodbank where email = :bb_mail"
        csr.execute(query,{'bb_mail':rmv_username})
        rslt = csr.fetchall()
        csr.close()

        if rslt and rslt == rmv_pass:

            rmv_csr = connection.cursor()
            rmv_query = "delete from bloodbank where email = :bb_mail"
            rmv_csr.execute(rmv_query,{'bb_mail' : rmv_username})
            rmv_csr.close()
            return render_template("info_page.html",common_info="Your acoount has been successfully removed")
                        
                            
        else:

            return "Invalid username or password please go back and try again"
        
    except cx_Oracle.DatabaseError as e:
        error_message = f"Database Error: {e}"
        return error_message  
                
    finally:
        connection.close() 


"""--------------------------------------------------"""
"""  Patient account removing """
"""--------------------------------------------------"""

@app.route('/smt_rmv_patient',methods = ["POST","GET"])
def smt_rmv_patient():


    connection = cx_Oracle.connect(orcl_connect_str)
    try:
        
        rmv_username = request.form['rmv_pt_mail']
        rmv_pass = request.form['rmv_pt_pass']
        
        csr = connection.cursor()
        query = f"select password from patient where email = '{rmv_username}'"
        csr.execute(query)
        rslt = csr.fetchone()
        csr.close()

        if rslt and rslt[0] == rmv_pass:

            rmv_csr = connection.cursor()
            rmv_query = "delete from patient where email = :pt_mail"
            rmv_csr.execute(rmv_query,{'pt_mail' : rmv_username})
            rmv_csr.close()
            return render_template("info_page.html",common_info="Your acoount has been successfully removed")

            
        else:

            return "Invalid useranme or password"

    except cx_Oracle.DatabaseError as e:
        error_message = f"Database Error: {e}"
        return error_message  
                
    finally:
        connection.close()


"""---------------------------------------------------"""  
""" Doner blood donation operation"""
"""---------------------------------------------------"""



@app.route('/donate_blood', methods=["POST", "GET"])
def donate_blood():
    try:
        if request.method == 'POST':
            d_mail = session.get('email')
            d_bb_name = request.form['bbank']

            connection = cx_Oracle.connect(orcl_connect_str)
            cursor1 = connection.cursor()
            query1 = f"SELECT id, name FROM bloodbank WHERE name = '{d_bb_name}'"
            cursor1.execute(query1)
            bb_result = cursor1.fetchall()
            cursor1.close()

            # Fetching values from the first cursor
            bb_id = bb_result[0][0] if bb_result else None
            bb_name = bb_result[0][1] if bb_result else None

            cursor2 = connection.cursor()
            query2 = f"SELECT id, name, blood_grp, last_donation_date FROM doner WHERE email = '{d_mail}'"
            cursor2.execute(query2)
            d_result = cursor2.fetchall()
            cursor2.close()

            # fetching all values
            d_id = d_result[0][0] if d_result else None
            d_name = d_result[0][1] if d_result else None
            d_blood_grp = d_result[0][2] if d_result else None
            d_ls_date = d_result[0][3] if d_result else None

            if d_ls_date is None or (datetime.now().date() - d_ls_date.date()).days > 55:

                cursor3 = connection.cursor()
                query3 = f"INSERT INTO available_bloods (bb_id, bb_name, d_id, d_name, d_bloodgrp, d_date) VALUES (:bb_id, :bb_name, :d_id, :d_name, :d_blood_grp, TO_DATE(:d_date, 'YYYY-MM-DD'))"
                cursor3.execute(query3, {'bb_id': bb_id, 'bb_name': bb_name, 'd_id': d_id, 'd_name': d_name, 'd_blood_grp': d_blood_grp, 'd_date': str(datetime.now().date())})
                connection.commit()
                cursor3.close()
                connection.close()

                connection = cx_Oracle.connect(orcl_connect_str)
                cursor4 = connection.cursor()
                query4 = f"UPDATE doner SET last_donation_date = TO_DATE(:d_date, 'YYYY-MM-DD') WHERE id = :d_id"
                cursor4.execute(query4, {'d_date': str(datetime.now().date()), 'd_id': d_id})
                connection.commit()
                cursor4.close()
                connection.close()
                return "Your response has been sent to the appropriate blood bank. Please contact the blood bank for further actions."
            else:
                return render_template('donerdonationpage.html', d_info=f"You have to wait atleast 56 days from the date of your last donation to donate ypur blood again.your last donation date {d_ls_date.date()}.")
        else:
            return render_template('donerdonationpage.html', d_info="Invalid request.")
    except cx_Oracle.DatabaseError as e:
        error_message = f"Database Error: {e}"
        return error_message

"""--------------------------------------------------"""
""" Patient search for blood"""
"""--------------------------------------------------"""


"""---------------------------------------------case 1--------------------------------"""


# @app.route('/search_for_blood', methods=["POST", "GET"])
# def search_for_blood():

#     connection = cx_Oracle.connect(orcl_connect_str)
    
#     try:
#         if request.method == 'POST':
#             pt_mail = session.get('email')
#             cursor2 = connection.cursor()
#             query2 = f"SELECT id, name, blood_grp, doner FROM patient WHERE email = '{pt_mail}'"
#             cursor2.execute(query2)
#             d_result = cursor2.fetchall()
#             cursor2.close()

#             pt_id, pt_name, pt_blood_grp, pt_doner = (d_result[0][0], d_result[0][1], d_result[0][2], d_result[0][3]) if d_result else (None, None, None, None)

#             if pt_doner is None or pt_doner.strip() == "":
#                 cursor1 = connection.cursor()
#                 query1 = f"SELECT * FROM available_bloods WHERE d_bloodgrp = '{pt_blood_grp}'"
#                 cursor1.execute(query1)
#                 blood_result = cursor1.fetchone()
#                 cursor1.close()

#                 bb_id, bb_name, d_id, d_name, d_bd_grp, d_date = (blood_result[0], blood_result[1], blood_result[2], blood_result[3], blood_result[4], blood_result[5]) if blood_result else (None, None, None, None, None, None)

#                 if pt_blood_grp == d_bd_grp:
#                     cursor4 = connection.cursor()
#                     query4 = f"UPDATE patient SET doner = '{d_id}' WHERE id = '{pt_id}'"
#                     cursor4.execute(query4)
#                     connection.commit()
#                     cursor4.close()

#                     cursor3 = connection.cursor()
#                     query3 = f"INSERT INTO blood_transfer_history (bb_id, bb_name, d_id, pt_id, bloodgrp, claim_date) VALUES (:bb_id, :bb_name, :d_id, :pt_id, :blood_grp, TO_DATE(:c_date, 'YYYY-MM-DD'))"
#                     cursor3.execute(query3, {'bb_id': bb_id, 'bb_name': bb_name, 'd_id': d_id, 'pt_id': pt_id, 'blood_grp': pt_blood_grp, 'c_date': str(datetime.now().date())})
#                     connection.commit()
#                     cursor3.close()

#                     rmv_csr = connection.cursor()
#                     rmv_query = "delete from patient where email = :pt_mail"
#                     rmv_csr.execute(rmv_query,{'pt_mail' : pt_mail})
#                     rmv_csr.close()
                    
#                     return render_template('patient_page.html', search_info=f"You got blood in {bb_name}, ID: {bb_id}. Get further details in the above table and VISIT BLOODBANK TODAY")
                
#                 elif pt_blood_grp != d_bd_grp:

#                     return render_template('patient_page.html',search_info="your bloodgroup is not available now,please wait for some time and search again ")
            
#             elif pt_doner is not None:

#                 connection = cx_Oracle.connect(orcl_connect_str)
#                 cursor5 = connection.cursor()
#                 query5 = f"SELECT bb_id, bb_name FROM blood_transfer_history WHERE pt_id = '{pt_id}'"
#                 cursor5.execute(query5)
#                 hstry_result = cursor5.fetchone()
#                 cursor5.close()



"""--------------case 2-------------------------------"""


# @app.route('/search_for_blood', methods=["POST", "GET"])
# def search_for_blood():

#     connection = cx_Oracle.connect(orcl_connect_str)

#     try:
#         if request.method == 'POST':
#             pt_mail = session.get('email')

#             # Get patient information
#             cursor2 = connection.cursor()
#             query2 = f"SELECT id, name, blood_grp, doner FROM patient WHERE email = :pt_mail"
#             cursor2.execute(query2, {'pt_mail': pt_mail})
#             d_result = cursor2.fetchone()
#             cursor2.close()

#             pt_id, pt_name, pt_blood_grp, pt_doner = (d_result[0], d_result[1], d_result[2], d_result[3]) if d_result else (None, None, None, None)

#             if pt_doner is None or pt_doner.strip() == "":  # Check if a donor is already assigned
#                 # Find available blood
#                 cursor1 = connection.cursor()
#                 query1 = f"SELECT * FROM available_bloods WHERE d_bloodgrp = :pt_blood_grp"
#                 cursor1.execute(query1, {'pt_blood_grp': pt_blood_grp})
#                 blood_result = cursor1.fetchone()
#                 cursor1.close()

#                 bb_id, bb_name, d_id, d_name, d_bd_grp, d_date = (blood_result[0], blood_result[1], blood_result[2], blood_result[3], blood_result[4], blood_result[5]) if blood_result else (None, None, None, None, None, None)

#                 if pt_blood_grp == d_bd_grp:  # Blood is available
#                     # Allocate blood
#                     cursor4 = connection.cursor()
#                     query4 = f"UPDATE patient SET doner = :d_id, status = 'ALLOCATED' WHERE id = :pt_id"  # Update status instead of deleting
#                     cursor4.execute(query4, {'d_id': d_id, 'pt_id': pt_id})
#                     connection.commit()
#                     cursor4.close()

#                     cursor3 = connection.cursor()
#                     query3 = f"INSERT INTO blood_transfer_history (bb_id, bb_name, d_id, pt_id, bloodgrp, claim_date) VALUES (:bb_id, :bb_name, :d_id, :pt_id, :blood_grp, TO_DATE(:c_date, 'YYYY-MM-DD'))"
#                     cursor3.execute(query3, {'bb_id': bb_id, 'bb_name': bb_name, 'd_id': d_id, 'pt_id': pt_id, 'blood_grp': pt_blood_grp, 'c_date': str(datetime.now().date())})
#                     connection.commit()
#                     cursor3.close()

#                     #deleting available bloods row 
#                     cursor7 = connection.cursor()
#                     query7 = f"delete from available_bloods where bb_id = '{bb_id} and d_id = '{d_id}' and pt_id = '{pt_id}' "
#                     cursor7.execute(query7)
#                     connection.commit()
#                     cursor7.close()

#                     return render_template('patient_page.html', search_info=f"You got blood in {bb_name}, ID: {bb_id}. Get further details in the above table and VISIT BLOODBANK TODAY")

#                 else:  # Blood not available
#                     return render_template('patient_page.html', search_info="Your blood group is not available now, please wait for some time and search again")

#             elif pt_doner is not None:  # Donor already assigned
#                 cursor5 = connection.cursor()
#                 query5 = f"SELECT bb_id, bb_name FROM blood_transfer_history WHERE pt_id = :pt_id"
#                 cursor5.execute(query5, {'pt_id': pt_id})
#                 hstry_result = cursor5.fetchone()
#                 cursor5.close()
#                 bid = hstry_result[0]

#                 bid = hstry_result[0]
#                 bname = hstry_result[1]

#                 return render_template('patient_page.html', search_info=f"You got blood in {bname}, ID: {bid}. Get further details in the above table and VISIT BLOODBANK TODAY")

                    
#     except cx_Oracle.DatabaseError as e:
#         error_message = f"Database Error: {e}"
#         return error_message  
                
#     finally:
#         connection.close()


"""----------------------case3-------------------------"""
@app.route('/search_for_blood', methods=["POST", "GET"])
def search_for_blood():
    connection = cx_Oracle.connect(orcl_connect_str)
    
    try:
        if request.method == 'POST':
            pt_mail = session.get('email')

            cursor2 = connection.cursor()
            query2 = f"SELECT id, name, blood_grp, doner FROM patient WHERE email = :pt_mail"
            cursor2.execute(query2, {'pt_mail': pt_mail})
            d_result = cursor2.fetchone()
            cursor2.close()

            pt_id, pt_name, pt_blood_grp, pt_doner = (d_result[0], d_result[1], d_result[2], d_result[3]) if d_result else (None, None, None, None)
            pt_id_ref = pt_id

            if pt_doner is None or pt_doner.strip() == "":
                cursor1 = connection.cursor()
                query1 = f"SELECT * FROM available_bloods WHERE d_bloodgrp = :pt_blood_grp"
                cursor1.execute(query1, {'pt_blood_grp': pt_blood_grp})
                blood_result = cursor1.fetchone()
                cursor1.close()

                bb_id, bb_name, d_id, d_name, d_bd_grp, d_date = (blood_result[0], blood_result[1], blood_result[2], blood_result[3], blood_result[4], blood_result[5]) if blood_result else (None, None, None, None, None, None)

                if pt_blood_grp == d_bd_grp:
                    # cursor4 = connection.cursor()
                    # query4 = f"UPDATE patient SET doner = :d_id WHERE id = :pt_id"
                    # cursor4.execute(query4, {'d_id': d_id, 'pt_id': pt_id_ref})
                    # connection.commit()
                    # cursor4.close()

                    # cursor8 = connection.cursor()
                    # query8 = f"INSERT INTO blood_transfer_history (bb_id, bb_name, d_id, pt_id, bloodgrp, claim_date) VALUES (:bb_id, :bb_name, :d_id, :pt_id, :blood_grp, TO_DATE(:c_date, 'YYYY-MM-DD'))"
                    # cursor8.execute(query8, {'bb_id': bb_id, 'bb_name': bb_name, 'd_id': d_id, 'pt_id': pt_id, 'blood_grp': pt_blood_grp, 'c_date': str(datetime.now().date())})
                    # connection.commit()
                    # cursor8.close()

                    # cursor7 = connection.cursor()
                    # query7 = f"DELETE FROM available_bloods WHERE bb_id = :bb_id AND d_id = :d_id AND pt_id = :pt_id"
                    # cursor7.execute(query7, {'bb_id': bb_id, 'd_id': d_id, 'pt_id': pt_id_ref})
                    # connection.commit()
                    # cursor7.close()
                    cursor4 = connection.cursor()
                    query4 = f"UPDATE patient SET doner = :d_id WHERE id = :pt_id"  # Here, use 'pt_id_ref' instead of 'pt_id'
                    cursor4.execute(query4, {'d_id': d_id, 'pt_id': pt_id_ref})  # Use 'pt_id_ref' as a bind variable
                    connection.commit()
                    cursor4.close()

                    cursor8 = connection.cursor()
                    query8 = f"INSERT INTO blood_transfer_history (bb_id, bb_name, d_id, pt_id, bloodgrp, claim_date) VALUES (:bb_id, :bb_name, :d_id, :pt_id, :blood_grp, TO_DATE(:c_date, 'YYYY-MM-DD'))"
                    cursor8.execute(query8, {'bb_id': bb_id, 'bb_name': bb_name, 'd_id': d_id, 'pt_id': pt_id_ref, 'blood_grp': pt_blood_grp, 'c_date': str(datetime.now().date())})
                    connection.commit()
                    cursor8.close()

                    cursor7 = connection.cursor()
                    query7 = f"DELETE FROM available_bloods WHERE bb_id = :bb_id AND d_id = :d_id AND pt_id = :pt_id"  # Use 'pt_id_ref' instead of 'pt_id'
                    cursor7.execute(query7, {'bb_id': bb_id, 'd_id': d_id, 'pt_id': pt_id_ref})  # Use 'pt_id_ref' as a bind variable
                    connection.commit()
                    cursor7.close()

                    return render_template('patient_page.html', search_info=f"You got blood in {bb_name}, ID: {bb_id}. Get further details in the above table and VISIT BLOODBANK TODAY")

                else:
                    return render_template('patient_page.html', search_info="Your blood group is not available now, please wait for some time and search again")

            elif pt_doner is not None and pt_doner.strip() != "":

                cursor5 = connection.cursor()
                query5 = f"SELECT bb_id, bb_name FROM blood_transfer_history WHERE pt_id = '{pt_id_ref}'"
                cursor5.execute(query5)
                hstry_result = cursor5.fetchone()
                cursor5.close()

                bid = hstry_result[0] if hstry_result else None
                bname = hstry_result[1] if hstry_result else None
                
                return render_template('patient_page.html', search_info=f"You got blood in {bname}, ID: {bid}. Get further details in the above table and VISIT BLOODBANK TODAY")

    except cx_Oracle.DatabaseError as e:
        error_message = f"Database Error: {e}"
        return error_message  
    
    finally:
        connection.close()




# Driver code
if __name__ == "__main__":

    app.run(debug=True)