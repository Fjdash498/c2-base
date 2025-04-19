import multiprocessing
import time
#Custom
from database.database import Database
from server.flask import Builder


"""
 - Set up background jobs to clean up stale database entries.
"""

def scrub_loop(db):
    print("scrubbing the floors.......")
    scrubS = multiprocessing.Process(target=db.scrub_table, args=("sessions",))
    scrubZ = multiprocessing.Process(target=db.scrub_table, args=("zombies",))
    scrubC = multiprocessing.Process(target=db.scrub_table, args=("commands",))
    scrubD = multiprocessing.Process(target=db.scrub_table, args=("data",))
    # print("SCRUB_LOOP => starting scrub workers")
    scrubZ.start()
    scrubS.start()
    scrubC.start()
    scrubD.start()
    scrubZ.join()
    scrubS.join()
    scrubC.join()
    scrubD.join()
    # print("SCRUB_LOOP => scrub should be done now")
    loop = multiprocessing.Process(target=scrub_loop,args=(db,))
    # print("SCRUB_LOOP => now sleeping 300")
    time.sleep(30)
    # print("SCRUB_LOOP => starting loop again")
    loop.start()
    loop.join()

def init_server():

    db = Database()
    # Build workers to periodically scrub tables.
    scrub = multiprocessing.Process(target=scrub_loop, args=(db,))
    scrub.start()
    # Setup Database and start app
    res = db.init()
    if res is False:
        # print("FATAL ERROR, COULDN'T INIT DB")
        exit()
    else:
        # Handle setting up the flask app
        app = Builder()
        app.run()


if __name__ == "__main__":
    app = init_server()
    app.run(port=8080)
