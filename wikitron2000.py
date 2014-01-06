#
# Convert wiki markup drupal entries to html
#

import MySQLdb
import creds
import urllib

db = MySQLdb.connect(host="127.0.0.1", port=3306, user=creds.mysql_user, passwd=creds.mysql_pass, db="dorkbotpdx")
cur = db.cursor() 
cur.execute("""SELECT n.nid, n.title, ff.name FROM node n 
			JOIN node_revisions nr ON n.nid = nr.nid AND n.vid = nr.vid 
			JOIN filter_formats ff ON nr.format = ff.format 
			WHERE ff.name = "Mediawiki" 
			ORDER BY n.nid;""")

def fetch_body(cur, nid):
	print("Fetching body...")
	cur.execute("SELECT vid,uid,body from node_revisions where nid = %(nid)s order by vid desc limit 1;", {'nid': nid})
	row = cur.fetchall()[0]
	return (row[0], row[1], row[2])

for row in cur.fetchall() :
	(nid, title) = (row[0], row[1])
	print("Processing node %s:  %s" %(nid, title))
	(vid, uid, body) = fetch_body(cur, nid)
	
	#parts = urllib.urlencode({'
