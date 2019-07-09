
from abc import ABC, abstractmethod
# from .file_retriever import FileRetriever


from dataclasses import dataclass, field
from typing import List
from typeguard import typechecked



@dataclass
class BaseText(ABC):
    """ Interface class for text data"""
    def __post_init__(self):
        """ check mapping """
        for k, v in self._key_class_mapping().items():
            assert isinstance(v(), BaseText)

    @abstractmethod
    def _key_class_mapping(self):
        return {}

    def load_dict(self, d):
        mapping = self._key_class_mapping()
        for key, item in d.items():
            if key in mapping:
                self.__dict__[key] = [ mapping[key]().load_dict(_t) for _t in item]
            elif key in self.__dict__:
                self.__dict__[key] = item
        return self

    def to_dict(self):
        d = {}
        for key, item in self.__dict__.items():
            if isinstance(item, list):
                d[key] = [ _item.to_dict() for _item in item]
            else:
                d[key] = item
        return d

@typechecked
@dataclass
class Annotation(BaseText):
    start_pos : int = 0
    end_pos : int = 0
    type : str = ""
    text : str = ""
    confidence : float = 0.0

    def _key_class_mapping(self):
        return {}

@typechecked
@dataclass
class Token(BaseText):
    text : str = ""
    index: int = 0
    annotations: List[Annotation] = field(default_factory=list)

    def _key_class_mapping(self):
        return {'annotations': Annotation}


@typechecked
@dataclass
class Sentence(BaseText):
    text : str = ""
    index: int = 0
    tokens : List[Token] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)

    def _key_class_mapping(self):
        return {'annotation': Annotation, "tokens": Token}

    def __iter__(self):
        for x in self.tokens:
            yield x


@typechecked
@dataclass
class Document(BaseText):
    title: str = ""
    text : str = ""
    url : str = ""
    id : str = ""
    sentences: List[Sentence] = field(default_factory=list)
    annotations: List[Annotation] = field(default_factory=list)

    def _key_class_mapping(self):
        return {'annotation': Annotation, "sentences": Sentence}

    def __iter__(self):
        for x in self.sentences:
            yield x


if __name__ == "__main__":

    s1 = 'Computer vision is an interdisciplinary scientific field .'
    tokens1 = [ Token(string, index) for index, string in enumerate(s1.split())]
    sent1 = Sentence('', 0, tokens1)

    s2 = 'Natural language processing is a subfield of computer science'
    tokens2 = [ Token(string, index) for index, string in enumerate(s2.split())]
    sent2 = Sentence('', 1, tokens2)

    doc = Document(sentences=[sent1, sent2])

    print(doc.to_dict())
    import pprint
    import json

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(doc.to_dict())

    for sent in doc:
        for tok in sent:
            print(tok)
    
    doc2 = Document().load_dict(doc.to_dict())
    pp.pprint(doc2.to_dict())
    d_doc2 = doc2.to_dict()
    str_json = json.dumps(d_doc2)
    print(str_json, type(str_json))
    d3 = json.loads(str_json)
    doc3 = Document().load_dict(d3)
    print(doc3)
    print(doc3.to_dict())