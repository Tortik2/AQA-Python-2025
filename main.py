import os
from xml.etree import ElementTree as ET
import json
INPUT_XML = "test_input.xml"
OUT_DIR = "out"
CONFIG_FILE = os.path.join(OUT_DIR, "config.xml")
META_FILE = os.path.join(OUT_DIR, "meta.json")
class ModelUnit:
    def __init__(self, tag, is_main, doc):
        self.tag = tag  # имя класса
        self.is_main = is_main  # корневой ли класс
        self.doc = doc  # документация
        self.fields = []  # список атрибутов
        self.nested = []  # вложенные классы (по агрегации)
    def make_config_xml(self):
        # XML для config.xml
        elem = ET.Element(self.tag)
        for field in self.fields:
            child_elem = ET.SubElement(elem, field["name"])
            child_elem.text = field["type"]
        for sub_model in self.nested:
            elem.append(sub_model.make_config_xml())
        return elem
    def make_meta_json(self, links):
        # meta.json
        block = {
            "class": self.tag,
            "documentation": self.doc,
            "isMain": self.is_main,
            "parameters": [
                {"name": f["name"], "type": f["type"]}
                for f in self.fields
            ]
        }
        if self.tag in links:
            block["parameters"] += [
                {"name": item.tag, "type": "class"}
                for item in self.nested
            ]
            block["min"] = links[self.tag]["min"]
            block["max"] = links[self.tag]["max"]
        return block
def parse_source(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    units = {}
    links = []
    # Считываем классы
    for node in root.findall("Class"):
        tag = node.attrib["name"]
        is_main = node.attrib.get("isRoot", "false") == "true"
        doc = node.attrib.get("documentation", "")
        model = ModelUnit(tag, is_main, doc)
        for attr in node.findall("Attribute"):
            model.fields.append({
                "name": attr.attrib["name"],
                "type": attr.attrib["type"]
            })
        units[tag] = model
    # связи между классами
    relation_map = {}
    for agg in root.findall("Aggregation"):
        who = agg.attrib["source"]
        to = agg.attrib["target"]
        how_many = agg.attrib["sourceMultiplicity"]
        min_val, max_val = (how_many.split("..") + [how_many])[:2] if ".." in how_many else (how_many, how_many)
        units[to].nested.append(units[who])
        if to not in relation_map:
            relation_map[to] = {"min": "1", "max": "1"}
        relation_map[who] = {"min": min_val, "max": max_val}
    return units, relation_map
def save_files(models, relations):
    os.makedirs(OUT_DIR, exist_ok=True)
    # config.xml
    for m in models.values():
        if m.is_main:
            root_elem = m.make_config_xml()
            ET.ElementTree(root_elem).write(CONFIG_FILE, encoding="unicode")
            break
    # meta.json
    meta_dump = [m.make_meta_json(relations) for m in models.values()]
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta_dump, f, indent=4)
if __name__ == "__main__":
    all_units, rels = parse_source(INPUT_XML)
    save_files(all_units, rels)
