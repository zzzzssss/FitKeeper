import json, pymysql, datetime, numpy, os

# path of db_info.json
db_info_filename_2 = os.path.join(os.path.dirname(__file__), 'db_info_shuyang.json')


# Read RDS info from file, connect to DB.
try:
    with open(db_info_filename_2) as db_info_file_2:
        db_info_2 = json.load(db_info_file_2)
        db_info_file_2.close()
except IOError:
    with open('db_info_shuyang.json') as db_info_file_2:
        print "[db_funcs_machines.py]IO Error???"
        db_info_2 = json.load(db_info_file_2)
        db_info_file_2.close()


def connect_db_2():
    """
    Connect to AWS RDS database.
    """
    db = pymysql.connect(
        db_info_2['host'],
        db_info_2['username'],
        db_info_2['password'],
        db_info_2['db']
    )
    return db

def find_STRIDE(db, start_time, end_time):
    """
    Query table STRIDE,
    Input:
        start_time: start time
        end_time: end time
    Return:
        Query result
    """
    a=((1000, datetime.timedelta(0, 28800), datetime.timedelta(0, 30600), 's100', 1),)
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM STRIDE \
                     WHERE start_time>=CAST(%s AS time)\
                     AND end_time<=CAST(%s AS time) \
                     AND is_available = TRUE",
                     (str(start_time), str(end_time),))
        result = cur.fetchall()
        cur.close()
        return result
    except:
        print "Failed to find stride machine. Return default value instead."
        return a

def find_ELIPTICAL(db, start_time, end_time):
    """
    Query table ELIPTICAL,
    Input:
        start_time: start time
        end_time: end time
    Return:
        Query result
    """
    a=((1000, datetime.timedelta(0, 39600), datetime.timedelta(0, 41400), 'e100', 1),)
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM ELIPTICAL \
                     WHERE start_time>=CAST(%s AS time)\
                     AND end_time<=CAST(%s AS time) \
                     AND is_available = TRUE",
                     (str(start_time), str(end_time),))
        result = cur.fetchall()
        cur.close()
        return result
    except:
        print "Failed to find ELIPTICAL machine. Return default value instead."
        return a



def find_STRENGTH(db, start_time, end_time):
    """
    Query table strength,
    Input:
        start_time: start time
        end_time: end time
    Return:
        Query result
    """
    a=((1000, datetime.timedelta(0, 39600), datetime.timedelta(0, 41400), 'm100', 1),)
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM STRENGTH \
                     WHERE start_time>=CAST(%s AS time)\
                     AND end_time<=CAST(%s AS time) \
                     AND is_available = TRUE",
                     (str(start_time), str(end_time),))
        result = cur.fetchall()
        cur.close()
        return result
    except:
        print "Failed to find strength machine. Return default value instead."
        return a


def find_machine_record(db, id):
    """
    Query table machineRESERV,
    Input:
        uid: uid
    Return:
        Query result
    """
    a=(('108153423178355183644', datetime.timedelta(0, 61200), datetime.timedelta(0, 63000), 'strength', 'm10'),)
    cur = db.cursor()
    try:
        cur.execute("SELECT * FROM machineRESERVE \
                     WHERE uid = %s",
                     (str(id),))
        result = cur.fetchall()
        cur.close()
        return result
    except:
        print "Failed to find machine record. Return default value instead."
        return a



def insert_machineRESERVE(db, uid, start_time, end_time, machine_type, machine_number):
    """
    use with update_strideAVALABLE,update_strengthAVALABLE,update_strengthAVALABLE
    """
    cur = db.cursor()
    try:
        cur.execute(
                    "INSERT INTO machineRESERVE \
                    (uid, start_time, end_time,machine_type,machine_number) \
                    VALUES (%s, %s, %s, %s, %s)",
                    (str(uid), str(start_time), str(end_time),str(machine_type),str(machine_number),))
        db.commit()
        # print "insert insert_machineRESERVE"
    except:
            db.rollback()
            print 'Failed to insert machine reservation table. Database rollback.'
    cur.close()
    return None

def delete_machineRESERVE(db, uid, start_time, end_time, machine_number):
    cur = db.cursor()
    try:
        cur.execute(
                    "DELETE FROM machineRESERVE WHERE start_time=CAST(%s AS time) AND end_time=CAST(%s AS time) AND uid = %s AND machine_number=%s", (str(start_time), str(end_time),str(uid),str(machine_number),))
        db.commit()
        print "delete delete_machineRESERV"
    except:
        db.rollback()
        print "delete machine resercation failed. Rollback Database."

    cur.close()
    return None



def update_strideAVALABLE(db, start_time, end_time, machine_number):
    cur = db.cursor()
    try:
        cur.execute(
                    "UPDATE STRIDE SET is_available = FALSE WHERE start_time=CAST(%s AS time) AND end_time=CAST(%s AS time) AND machine_number=%s", (str(start_time), str(end_time),str(machine_number),))
        db.commit()
        print "updated update_strideAVALABLE"
    except:
        db.rollback()
        print "stride machine Update availibility failed. Rollback Database."
    cur.close()
    return None

def update_elipticalAVALABLE(db, start_time, end_time, machine_number):
    cur = db.cursor()
    try:
        cur.execute(
                    "UPDATE ELIPTICAL SET is_available = FALSE WHERE start_time=CAST(%s AS time) AND end_time=CAST(%s AS time) AND machine_number=%s", (str(start_time), str(end_time),str(machine_number),))
        db.commit()
        print "updated update_elipticalAVALABLE"
    except:
        db.rollback()
        print "eliptical machine Update availibility failed. Rollback Database."

    cur.close()
    return None

def update_strengthAVALABLE(db, start_time, end_time, machine_number):
    cur = db.cursor()
    try:
        cur.execute(
                    "UPDATE STRENGTH SET is_available = FALSE WHERE start_time=CAST(%s AS time) AND end_time=CAST(%s AS time) AND machine_number=%s", (str(start_time), str(end_time),str(machine_number),))
        db.commit()
        print "updated update_elipticalAVALABLE"
    except:
        db.rollback()
        print "strength machine Update availibility failed. Rollback Database."

    cur.close()
    return None

def cancel_strideAVALABLE(db, start_time, end_time, machine_number):
    cur = db.cursor()
    try:
        cur.execute(
                    "UPDATE STRIDE SET is_available = TRUE WHERE start_time=CAST(%s AS time) AND end_time=CAST(%s AS time) AND machine_number=%s", (str(start_time), str(end_time),str(machine_number),))
        db.commit()
        print "cancel strideAVALABLE"
    except:
        db.rollback()
        print "stride machine cancel availibility failed. Rollback Database."

    cur.close()
    return None

def cancel_elipticalAVALABLE(db, start_time, end_time, machine_number):
    cur = db.cursor()
    try:
        cur.execute(
                    "UPDATE ELIPTICAL SET is_available = TRUE WHERE start_time=CAST(%s AS time) AND end_time=CAST(%s AS time) AND machine_number=%s", (str(start_time), str(end_time),str(machine_number),))
        db.commit()
        print "cancel elipticalAVALABLE"
    except:
        db.rollback()
        print "eliptical machine cancel availibility failed. Rollback Database."

    cur.close()
    return None

def cancel_strengthAVALABLE(db, start_time, end_time, machine_number):
    cur = db.cursor()
    try:
        cur.execute(
                    "UPDATE STRENGTH SET is_available = TRUE WHERE start_time=CAST(%s AS time) AND end_time=CAST(%s AS time) AND machine_number=%s", (str(start_time), str(end_time),str(machine_number),))
        db.commit()
        print "cancel strengthlAVALABLE"
    except:
        db.rollback()
        print "strength machine cancel availibility failed. Rollback Database."
    cur.close()
    return None


def find_machineRESERVE(db, uid):
    cur = db.cursor()
    a=(('108153423178355183644', datetime.timedelta(0, 0), datetime.timedelta(0, 0), 'strength', 'm100'),)
    try:
        cur.execute("SELECT * FROM machineRESERVE \
                     WHERE uid = %s",
                     (str(uid),))
        result = cur.fetchall()
        cur.close()
        return result
    except:
        print "Failed to find machine reserve. Return default value instead."
        return a




# if __name__ == '__main__':
db_2 = connect_db_2()
# result=find_machine_record(db_2, '108153423178355183644')
# print result
# result=find_STRENGTH(db_2,'11:00:00','11:30:00')
# print result
# insert_machineRESERVE(db_2, '108153423178355183644','11:00:00','11:30:00','Stride','s1')
# insert_machineRESERVE(db_2, '108153423178355183644','12:00:00','12:30:00','Stride','s2')
# insert_machineRESERVE(db_2, '108153423178355183644','15:00:00','15:30:00','Strength','m1')
# insert_machineRESERVE(db_2, '108153423178355183644','16:00:00','16:30:00','Strength','m2')
# insert_machineRESERVE(db_2, '108153423178355183644','14:00:00','14:30:00','Eliptical','e1')
# delete_machineRESERVE(db_2, '108153423178355183644','11:00:00','11:30:00','Stride','s1')
# update_strengthAVALABLE(db_2,'11:00:00','11:30:00','m1')
# update_elipticalAVALABLE(db_2,'11:00:00','11:30:00','e1')
# update_strideAVALABLE(db_2,'11:00:00','11:30:00','s1')
# result=find_machineRESERVE(db_2, '108153423178355183644')
# print result

    