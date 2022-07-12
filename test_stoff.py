from standoffconverter import Standoff, View
from lxml import etree
import spacy
import pandas as pd

from sqlalchemy import create_engine

pos_table_engine = create_engine('sqlite:///my_test_store.db')


name_table = "test_table"

xml = "./datatest/dahn/Lettre569_3octobre1919.xml"

tree = etree.parse(xml)

so = Standoff(tree, namespaces={"tei":"http://www.tei-c.org/ns/1.0"})

view = (
    View(so)
        .shrink_whitespace()
        .insert_tag_text("http://www.tei-c.org/ns/1.0}lb","\n")
)

df = view.view

df.drop('el', inplace=True, axis=1)
df.to_sql('test_table', pos_table_engine, if_exists='append')

df_2 = pd.read_sql_query(f'SELECT * FROM {name_table}', pos_table_engine)

def get_pos(df, i):
    index = (df.char.apply(len).cumsum()-1==i).argmax()
    return df.iloc[index].table_position

nlp = spacy.load('fr_core_news_lg')

for ent in nlp(view.get_plain()).ents:
    start_ind = get_pos(df_2, ent.start_char)
    end_ind = get_pos(df_2, ent.end_char)
    print(ent.text, ent.label_, start_ind, end_ind)


#print(type(plain))