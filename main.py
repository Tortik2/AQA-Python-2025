import os
from xml.etree import ElementTree as ET
import json

INPUT_FILE = "test_input.xml"
OUTPUT_DIR = "out"
CONFIG_XML = os.path.join(OUTPUT_DIR, "config.xml")
META_JSON = os.path.join(OUTPUT_DIR, "meta.json")
class UMLClass:
    def __init__(self, name, is_root, documentation):
        self.name = name
        self.is_root = is_root
        self.documentation = documentation
        self.attributes = []  
        self.children = []    

    def to_config_xml(self): #Рекурсивно формируем XML-элемент
        elem = ET.Element(self.name)
        for attr in self.attributes:
            child = ET.SubElement(elem, attr["name"])
            child.text = attr["type"]
        for child_class in self.children:
            elem.append(child_class.to_config_xml())
        return elem
    
    def to_meta_json(self, class_relations): #Формируем словарь мета-информации
        meta = {
            "class": self.name,
            "documentation": self.documentation,
            "isRoot": self.is_root,
            "parameters": [
                {"name": attr["name"], "type": attr["type"]}
                for attr in self.attributes
            ]
        }
        if self.name in class_relations:
            meta["parameters"] += [
                {"name": child.name, "type": "class"}
                for child in self.children
            ]
            meta["min"] = class_relations[self.name]["min"]
            meta["max"] = class_relations[self.name]["max"]
        return meta
# Функция парсинга входного XML-файла
def parse_input(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    classes = {}
    aggregations = []
    # Извлекаем классы
    for elem in root.findall("Class"):
        name = elem.attrib["name"]
        is_root = elem.attrib.get("isRoot", "false") == "true"
        documentation = elem.attrib.get("documentation", "")
        uml_class = UMLClass(name, is_root, documentation)
        for attr in elem.findall("Attribute"):
            uml_class.attributes.append({
                "name": attr.attrib["name"],
                "type": attr.attrib["type"]
            })
        classes[name] = uml_class
    # Извлекаем агрегации (связи между классами)
    class_relations = {}
    for agg in root.findall("Aggregation"):
        source = agg.attrib["source"]
        target = agg.attrib["target"]
        src_mult = agg.attrib["sourceMultiplicity"]
        min_val, max_val = (src_mult.split("..") + [src_mult])[:2] if ".." in src_mult else (src_mult, src_mult)

        classes[target].children.append(classes[source])
        if target not in class_relations:
            class_relations[target] = {"min": "1", "max": "1"}
        class_relations[source] = {"min": min_val, "max": max_val}
    return classes, class_relations
# Функция генерации выходных файлов
def generate_output(classes, class_relations):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    #config.xml
    for cls in classes.values():
        if cls.is_root:
            root_element = cls.to_config_xml()
            tree = ET.ElementTree(root_element)
            tree.write(CONFIG_XML, encoding="unicode")
            break
    #meta.json
    meta = [cls.to_meta_json(class_relations) for cls in classes.values()]
    with open(META_JSON, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)

if __name__ == "__main__":
    classes, class_relations = parse_input(INPUT_FILE)
    generate_output(classes, class_relations)