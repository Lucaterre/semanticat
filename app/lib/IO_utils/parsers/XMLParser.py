# -*- coding: UTF-8 -*-

import re

import cchardet
from lxml import etree

from app.lib.standoffconverter import (Standoff,
                                       View)


class XML:
    """Global wrapper class for XML.
    Check the conformity of XML.

    Parameters:
        source (str): Original XML.
    """
    def __init__(self, source):
        self.source = source
        self.allowed_schemas = ["tei", "ead"]
        try:
            self.tree = etree.fromstring(self.source)
            self.schema = re.sub(r'\{.*\}', '', str(etree.XML(self.source).tag)).lower()
            if self.schema not in self.allowed_schemas:
                self.schema = "error_schema"
        except etree.XMLSyntaxError:
            self.schema = "conformity_error"
        except Exception:
            self.schema = "error"


class XMLStrategiesParser(XML):
    """Class use to parse XML and use the best strategy for format to
    extract a plain text view.

    Parameters:
        source (str): Original XML.
    """
    def __init__(self, source):
        super().__init__(source)
        self.dids_level = None
        self.so = None
        self.view = None
        self.sentences = []
        self.plain_text = ""
        if self.schema == "ead":
            # Use ead_strategy() method
            self.dids_level, self.sentences = self.ead_strategy()
            self.plain_text = "\n".join(self.sentences)
        if self.schema == "tei":
            # Use Standoff Converter
            self.so = Standoff(self.tree, namespaces={"tei": "http://www.tei-c.org/ns/1.0"})
            self.view = (View(self.so).shrink_whitespace())
            self.plain_text = self.view.get_plain()
        else:
            pass

    def ead_strategy(self):
        """Specific wrapper to parse EAD files and build did container to create sentences"""
        # create a container for sentences and dids
        # elements
        sentences = []
        container_dids = []
        # get the <dsc> level
        dsc = self.tree.xpath('.//dsc')
        for chlidren_dsc in dsc:
            # get <did> levels
            for did in chlidren_dsc.xpath('.//did'):
                container_dids.append(did)
                text = ""
                if did is not None:
                    text += " ".join(
                        [did_content.strip() for did_content in did.itertext() if len(did_content) > 0])
                # get the scopecontent if exists and concatenate with the rest
                if did.getnext() is not None:
                    text += " ".join(
                        [" ".join(scopecontent.strip().split()) for scopecontent in did.getnext().itertext() if
                         len(scopecontent) > 0])
                sentences.append(" " + re.sub(r"\s{2,}", " ", text.strip()) + " ")
        # assert len(sentences) == len(container_dids)
        return container_dids, sentences
