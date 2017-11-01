#!/usr/bin/env python3

# http://habanero.readthedocs.io/en/latest/api.html

from habanero import Crossref as c
from habanero import counts
from habanero import cn

cites = counts.citation_count(doi="10.1371/journal.pone.0042793")

print('Number of Citations: %s' % cites)


cn.content_negotiation(ids = '10.1126/science.169.3946.635'


