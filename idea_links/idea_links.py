

"""
Looking at tinymongo
"""

import tinydb
from typing import List
import datetime
import re
import pandas as pd
import numpy as np
import markdown


DB_FN = 'idea_db.json'

db = tinydb.TinyDB(DB_FN)

class Idea:

    doc_id: int = None
    short_txt: str
    long_txt: str
    parents: List[int]
    childs:  List[int]
    related: List[int]
    relation_fields = ['parents', 'childs', 'related']

    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            kwargs['short_txt'] = args[0]

        for r in self.relation_fields:
            if r not in kwargs.keys():
                kwargs[r] = []
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"<Idea {self.doc_id}: {self.short_txt}>"

    def detail(self):
        long_txt = '' if not hasattr(self, 'long_txt') else self.long_txt
        s = f"""{self.short_txt}
Last Visit: {self.visited}

{long_txt}
"""
        for rel in self.relation_fields:
            if len(getattr(self, rel)) > 0:
                s += rel + ':\n'
                for n, doc_id in enumerate(getattr(self, rel)):
                    i = Idea.from_doc_id(doc_id)
                    s += f"{n}: {i}\n"
                s += "\n\n"
        print(s)

    def long_txt_html(self):
        return markdown.markdown(self.long_txt, extensions=['tables'])

    def save(self):
        self.visited = datetime.datetime.now().strftime('%y-%m-%d %H:%M')
        if self.doc_id is None:
            self.doc_id = db.insert(self.__dict__)
        else:
            tmp = dict(self.__dict__)
            if 'doc_id' in tmp.keys():
                del tmp['doc_id']
            for k, v in tmp.items():
                if k in self.relation_fields:
                    # Remove any duplicates
                    tmp[k] = list(set(v))
            #print(f"update id: {self.doc_id} {tmp}")
            db.update(tmp, doc_ids=[self.doc_id])

    def add_related(self, i: 'Idea'):
        if self.doc_id is None:
            self.save()

        if i.doc_id is None:
            i.save()

        self.related.append(i.doc_id)
        i.related.append(self.doc_id)
        self.save()
        i.save()
        return i

    def add_child(self, i: 'Idea'):
        if self.doc_id is None:
            self.save()

        if i.doc_id is None:
            i.save()

        self.childs.append(i.doc_id)
        i.parents.append(self.doc_id)
        self.save()
        i.save()
        return i

    def add_parent(self, i: 'Idea'):
        if self.doc_id is None:
            self.save()

        if i.doc_id is None:
            i.save()

        self.parents.append(i.doc_id)
        i.childs.append(self.doc_id)
        self.save()
        i.save()
        return i

    def get_child(self, n):
        return Idea.from_doc_id(self.childs[n])

    def get_childs(self):
        return [self.get_child(n) for n in range(len(self.childs))]

    def get_parent(self, n):
        return Idea.from_doc_id(self.parents[n])

    def get_parents(self):
        return [self.get_parent(n) for n in range(len(self.parents))]

    def get_related(self, n):
        return Idea.from_doc_id(self.related[n])

    def get_relateds(self):
        return [self.get_related(n) for n in range(len(self.related))]

    def check_relations(self):
        """
        Make sure relations are reciprocal
        :return:
        """
        if self.doc_id is None:
            self.save()

        for doc_id in self.related:
            i = Idea.from_doc_id(doc_id)
            if self.doc_id not in i.related:
                i.add_related(self)

        for doc_id in self.childs:
            i = Idea.from_doc_id(doc_id)
            if self.doc_id not in i.parents:
                i.add_parent(self)

        for doc_id in self.parents:
            i = Idea.from_doc_id(doc_id)
            if self.doc_id not in i.childs:
                i.add_child(self)

    @staticmethod
    def from_doc_id(doc_id):
        dbobj = db.get(doc_id=doc_id)
        i = Idea(**dbobj)
        i.doc_id = dbobj.doc_id
        return i

    @staticmethod
    def from_document(dbobj: 'tinydb.table.Document'):
        i = Idea(**dbobj)
        i.doc_id = dbobj.doc_id
        return i


def search(txt):
    txt = '.*' + txt + ".*"
    return [Idea.from_doc_id(result.doc_id) for result in
            db.search(tinydb.Query().short_txt.matches(txt, flags=re.IGNORECASE) |
                      tinydb.Query().long_txt.matches(txt, flags=re.IGNORECASE))]


def delete(i: 'Idea'):
    """
    Delete object and remove references
    :param i:
    :return:
    """
    for doc_id in i.parents:
        p = Idea.from_doc_id(doc_id)
        p.childs.remove(i.doc_id)
        p.save()

    for doc_id in i.childs:
        c = Idea.from_doc_id(doc_id)
        c.parents.remove(i.doc_id)
        c.save()

    for doc_id in i.parents:
        r = Idea.from_doc_id(doc_id)
        r.related.remove(i.doc_id)
        r.save()


def incr_df(df, doc_id, col):
    if (doc_id not in df.index):
        i = Idea.from_doc_id(doc_id)
        df.loc[doc_id, 'Name'] = i.short_txt
        df.loc[doc_id, col] = 1
    elif (doc_id in df.index) and np.isnan(df.loc[doc_id, col]):
        df.loc[doc_id, col] = 1
    else:
        df.loc[doc_id, col] += 1


def connections():
    df = pd.DataFrame()

    for idea in db.all():
        idea = Idea.from_document(idea)
        #import pdb; pdb.set_trace()
        for doc_id in idea.parents:
            incr_df(df, doc_id, 'parent')

        for doc_id in idea.childs:
            incr_df(df, doc_id, 'child')

        for doc_id in idea.related:
            if doc_id in [1, 14]:
                print(f"doc_id {doc_id}")
            incr_df(df, doc_id, 'related')

    return df
