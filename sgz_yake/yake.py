# -*- coding: utf-8 -*-

"""Main module."""

from nltk.tokenize.toktok import ToktokTokenizer
from spacy.lang.en import English

import string
import os
import jellyfish
from .Levenshtein import Levenshtein

from .datarepresentation import DataCore

class KeywordExtractor(object):

    def __init__(self, lan="en", n=3, dedupLim=0.9, dedupFunc='seqm', windowsSize=1, top=20, features=None, stopwords=None):
        self.toktok = ToktokTokenizer()
        self.nlp_senlist = English()
        sentencizer = self.nlp_senlist.create_pipe("sentencizer")
        self.nlp_senlist.add_pipe(sentencizer)

        self.lan = lan

        dir_path = os.path.dirname(os.path.realpath(__file__))

        local_path = os.path.join("StopwordsList", "stopwords_%s.txt" % lan[:2].lower())

        if os.path.exists(os.path.join(dir_path,local_path)) == False:
            local_path = os.path.join("StopwordsList", "stopwords_noLang.txt")
        
        resource_path = os.path.join(dir_path,local_path)

        if stopwords is None:
            try:
                with open(resource_path, encoding='utf-8') as stop_fil:
                    self.stopword_set = set( stop_fil.read().lower().split("\n") )
            except:
                print('Warning, read stopword list as ISO-8859-1')
                with open(resource_path, encoding='ISO-8859-1') as stop_fil:
                    self.stopword_set = set( stop_fil.read().lower().split("\n") )
        else:
            self.stopword_set = set(stopwords)

        self.n = n
        self.top = top
        self.dedupLim = dedupLim
        self.features = features
        self.windowsSize = windowsSize
        if dedupFunc == 'jaro_winkler' or dedupFunc == 'jaro':
            self.dedu_function = self.jaro
        elif dedupFunc.lower() == 'sequencematcher' or dedupFunc.lower() == 'seqm':
            self.dedu_function = self.seqm
        else:
            self.dedu_function = self.levs

    def jaro(self, cand1, cand2):
        return jellyfish.jaro_winkler(cand1, cand2 )

    def levs(self, cand1, cand2):
        return 1.-jellyfish.levenshtein_distance(cand1, cand2 ) / max(len(cand1),len(cand2))

    def seqm(self, cand1, cand2):
        return Levenshtein.ratio(cand1, cand2)

    def extract_keywords(self, text):
        text = text.replace('\n\t',' ')
        dc = DataCore(toktok_tokenizer=self.toktok,spacy_nlp_senlist=self.nlp_senlist,text=text, stopword_set=self.stopword_set, windowsSize=self.windowsSize, n=self.n)
        dc.build_single_terms_features(features=self.features)
        dc.build_mult_terms_features(features=self.features)
        resultSet = []
        todedup = sorted([cc for cc in dc.candidates.values() if cc.isValid()], key=lambda c: c.H)

        if self.dedupLim >= 1.:
            return ([ (cand.H, cand.unique_kw) for cand in todedup])[:self.top]

        for cand in todedup:
            toadd = True
            for (h, candResult) in resultSet:
                dist = self.dedu_function(cand.unique_kw, candResult.unique_kw)
                if dist > self.dedupLim:
                    toadd = False
                    break
            if toadd:
                resultSet.append( (cand.H, cand) )
            if len(resultSet) == self.top:
                break

        return [ (cand.unique_kw,h) for (h,cand) in resultSet]
