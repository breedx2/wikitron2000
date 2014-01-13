
wikitron2000
============

A hack to assist in migration away from Drupal mediawiki markup.  Reality is ugly.

So we have a community Drupal site with a bunch of users and a bunch of pages. 
Some of thoes pages are in Mediawiki markup format, but we want to migrate to 
Drupal 7 for some of the skinning features.  There is no current support for
Wiki or Mediawiki output "filters" in Drupal 7, so we have chosen to abandon it.
That sucks, but we must move forward.

So this is a hacked up script to help with the migration.  It's still hundreds hundreds of 
page conversions, but at least it's not 5-6 clicks per page....

Running it
==========

In the interest of not screwing up pages, I have not built something that migrates the
entire site.  It only does a node at a time and expects to be hand-held.

Create a python virtualenv:
`virtualenv --no-site-packages env`

Then activate it:
`source env/bin/activate`

Install the dependencies:
`$ sudo apt-get install libmysqlclient-dev`
`$ easy_install MySQL-python`


You will need to create `creds.py` in the directory and it should contain something like this:

```
mysql_user='your-super-secret-user'
mysql_pass='your-super-secret-pw'
```


Here is the commandline usage:

```
$ python wikitron2000.py --help
usage: wikitron2000.py [-h] [--nid <nid>] [--update]

Some drupal Mediawiki -> HTML conversion

optional arguments:
  -h, --help   show this help message and exit
  --nid <nid>  Specify the node id to munge
  --update     Go all the way and update the database
```

If your remote/site MySQL instance only listens on localhost (ours does), you may want to 
just tunnel SSH.  I do it like this:

`ssh -L 3306:localhost:3306 theremotewebsite.org`

And then finally you can run the script against a node.  I recommend looking at the node before/after running
the script to see how it worked.

Here is how the magic happens:

`$ python wikitron2000.py --update --nid 744`


Some notes
==========

Be aware of [img_assist|....] junk.  It messes things up.  Migrate those urls first if you please.

We use this to parse the wiki format into usable HTML:
http://www.mediawiki.org/wiki/API:Parsing_wikitext

It should be noted that this is not perfect for our hacked up kludge of a Drupal
configuration, so there are some pre/post parsing steps that know about 
some of our specific magic.

Perhaps a useful python parser:
https://github.com/dcramer/py-wikimarkup
(ended up not using, but could be cool)

Here's a query that will show all of our nodes that still use Mediawiki format:
```
SELECT n.nid, n.title, ff.name FROM node n 
JOIN node_revisions nr ON n.nid = nr.nid AND n.vid = nr.vid 
JOIN filter_formats ff ON nr.format = ff.format 
WHERE ff.name = "Mediawiki" 
ORDER BY n.nid;
```
