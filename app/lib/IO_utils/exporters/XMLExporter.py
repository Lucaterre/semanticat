# -*- coding: UTF-8 -*-

from os import path
import re

from lxml import etree, objectify

from app.config import PATH
from app.lib.IO_utils.parsers.XMLParser import XMLStrategiesParser
from app.models import (WordToken,
                        Sentence,
                        MappingNerLabel)


class XMLExporterStrategies(XMLStrategiesParser):
    """
    Class to create an XML exporter.

    Parameters:
        source (str): Original XML.
        document_id (int): Document identifier in database.
        project_id (int): Project identifier in database.
        type_xslt (bool): Flag for use XSLT or not as component of exporter. Defaults to `False`.
    """
    def __init__(self, source, document_id, project_id, type_xslt=False):
        """
        Constructor for XMLExporterStrategies class.
        """
        super().__init__(source)
        self.mapping_ner = MappingNerLabel.mapping_ner_as_dict(project_id=project_id)
        self.xslt_inline_annotations_filepath = path.join(PATH, "stylesheet/enhanced_xml.xslt")
        if self.schema == "tei" and not type_xslt:
            self.annotations = WordToken.query.filter_by(document_id=document_id).all()
            self.sentences = []
        if self.schema == "ead" and not type_xslt:
            self.annotations = []
            self.sentences = Sentence.return_all_sentences_for_document(doc_id=document_id)
        if type_xslt:
            self.glossary = WordToken.return_all_mentions_for_document(doc_id=document_id)
            self.labels = WordToken.return_all_labels_for_document(doc_id=document_id)
            self.mentions_labels = list(
                set(
                    [(mention, label) for mention, label in zip(
                        self.glossary,
                        self.labels)]
                )
            )
            self.map_labels = MappingNerLabel.mapping_ner_as_dict(project_id=project_id)

    def tei_results_to_inline_standoff(self):
        """Specific TEI Exporter using standoffconverter as component and export
        annotations inline.
        """
        for annotation in self.annotations:
            try:
                self.so.add_inline(
                    begin=self.view.get_table_pos(annotation.start),
                    end=self.view.get_table_pos(annotation.end),
                    tag=self.mapping_ner[annotation.label]['prefLabel'],
                    depth=None
                )
            except Exception:
                pass
        return etree.tostring(self.so.tree, encoding='unicode')

    def ead_results_to_controlaccess_level(self):
        """Specific EAD Exporter to export annotations in <controlaccess> level.
        """
        for sentence, did in zip(self.sentences, self.dids_level):
            self.annotations = WordToken.return_annotations_per_sentences_id(sentence_id=sentence[0])
            if len(self.annotations) > 0:
                parent = did.getparent()
                controlaccess = etree.Element('controlaccess')
                for annotation in self.annotations:
                    entity_tag = etree.Element(str(self.mapping_ner[annotation[0]]['prefLabel']))
                    entity_tag.text = annotation[1]
                    controlaccess.append(entity_tag)
                parent.append(controlaccess)

        return etree.tostring(self.tree, encoding='unicode')

    def results_to_inline_xslt(self):
        """Global (no specific schema) XML Exporter to export annotations inline with
        XSLT stylesheet component.
        """
        new = ""
        stylesheet = etree.XML("""
        <xsl:stylesheet version="1.0"
             xmlns:btest="uri:bolder"
             xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

            <xsl:template match="@* | node()">
              <xsl:copy>
                <xsl:apply-templates select="@* | node()"/>
              </xsl:copy>
            </xsl:template>

            <xsl:template match="text()">
                <xsl:copy-of select="btest:bolder(.)/node()" />
            </xsl:template>         
         </xsl:stylesheet>
        """)
        for mention, label in self.mentions_labels:
            new += str(re.escape(mention)) + "|"
            self.mapping_ner[mention] = label
        regex = r'({})'.format(new[:-1])

        def bolder(_, s):
            results = []
            splits = re.split(regex, s[0])

            for p, split in enumerate(splits):
                if p % 2 == 0:
                    el = etree.Element("element")
                    el.text = split
                else:
                    prefLabel = self.map_labels[self.mapping_ner[split]]["prefLabel"]
                    el = etree.Element("element")
                    entity = etree.SubElement(el, prefLabel)
                    entity.text = split
                results.append(el)
            return results

        # create a copy of original tree
        original_text = ""
        original_tree_part = ""
        original_tree = self.tree
        # Get the part want to adapt (TEI -> <text> / EAD -> <dsc>) and
        # the original text node want to modify
        # TEI
        if self.schema == "tei":
            original_tree_part = original_tree.xpath('.//tei:text',
                                                     namespaces={"tei": "http://www.tei-c.org/ns/1.0"})[0]
            original_text = etree.tostring(original_tree_part,
                                           pretty_print=True,
                                           encoding='utf-8',
                                           method='xml').decode("utf-8")
        # EAD
        elif self.schema == "ead":
            original_tree_part = original_tree.xpath('.//dsc')[0]
            original_text = etree.tostring(original_tree_part,
                                           pretty_print=True,
                                           encoding='utf-8',
                                           method='xml').decode("utf-8")

        # reference function in XSLT stylesheet
        ns = etree.FunctionNamespace('uri:bolder')
        ns['bolder'] = bolder

        # Instanciate transform
        transform = etree.XSLT(stylesheet)
        # Apply XSLT transform on text part want to modify
        out = transform(etree.XML(str(original_text)))

        original_tree_part.getparent().replace(original_tree_part, etree.fromstring(str(out)))

        # Replace part in original xml
        # print(etree.tostring(original_tree.replace(original_tree_part, etree.fromstring(str(out)))))

        # Clean empty namespaces from new elements
        objectify.deannotate(original_tree, xsi_nil=True)
        etree.cleanup_namespaces(original_tree)

        return etree.tostring(original_tree,
                              pretty_print=True,
                              encoding='utf-8',
                              method='xml',
                              xml_declaration=True).decode("utf-8")
