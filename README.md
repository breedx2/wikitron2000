

We will try and use this:
http://www.mediawiki.org/wiki/API:Parsing_wikitext

Perhaps a useful python parser:
https://github.com/dcramer/py-wikimarkup

Here's a query that will show all of our nodes that use Mediawiki format:
```
SELECT n.nid, n.title, ff.name FROM node n 
JOIN node_revisions nr ON n.nid = nr.nid AND n.vid = nr.vid 
JOIN filter_formats ff ON nr.format = ff.format 
WHERE ff.name = "Mediawiki" 
ORDER BY n.nid;
```
