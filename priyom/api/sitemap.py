import collections
import collections.abc

import lxml.etree as etree

import xsltea.processor
import xsltea.exec

from xsltea.namespaces import NamespaceMeta

class Node(collections.abc.MutableSequence):
    @classmethod
    def subnode(cls, parent, *args, **kwargs):
        node = cls(*args, **kwargs)
        parent.append(node)
        return node

    def __init__(self, routable=None, label=None, **kwargs):
        super().__init__(**kwargs)
        self.routable = routable
        self.label = label
        self.parent = None
        self._children = []

    def _release_child(self, obj):
        obj.parent = None

    def _release_children(self, sequence):
        collections.deque(0, map(self._release_child, sequence))

    def _validate_and_acquire_child(self, obj):
        if obj.parent is not None:
            raise ValueError("{} is already bound to parent {}".format(
                obj, obj.parent))
        obj.parent = self

    def _validate_and_acquire_children(self, sequence):
        collections.deque(0, map(self._validate_and_acquire_child, sequence))

    def __delitem__(self, index):
        if isinstance(index, slice):
            self._release_children(self._children[index])
        else:
            self._release_child(self._children[index])
        try:
            del self._children[index]
        except:
            if isinstance(index, slice):
                self._validate_and_acquire_children(self._children[index])
            else:
                self._validate_and_acquire_child(self._children[index])

    def __getitem__(self, index):
        return self._children[index]

    def __iter__(self):
        return iter(self._children)

    def __len__(self):
        return len(self._children)

    def __reversed__(self):
        return iter(reversed(self._children))

    def __setitem__(self, index, obj):
        if isinstance(index, slice):
            obj = list(obj)  # we must evaluate it here once
            self._validate_and_acquire_children(obj)
        else:
            self._validate_and_acquire_child(obj)
        try:
            self._children[index] = obj
        except:
            if isinstance(index, slice):
                self._release_children(obj)
            else:
                self._release_child(obj)

    def append(self, obj):
        self._validate_and_acquire_child(obj)
        try:
            self._children.append(obj)
        except:
            self._release_child(obj)
            raise

    def insert(self, index, obj):
        self._validate_and_acquire_child(obj)
        try:
            self._children.insert(index, obj)
        except:
            self._release_child(obj)
            raise

    def reverse(self):
        self._children.reverse()

    def pop(self, index=-1):
        obj = self._children.pop(index)
        self._release_child(obj)
        return obj

    def new(self, *args, **kwargs):
        return self.subnode(self, *args, **kwargs)

    def __repr__(self):
        return "<sitemap node: routable={!r}, len(children)={}, label={!r}>".format(
            self.routable,
            len(self),
            self.label)

class SitemapProcessor(xsltea.processor.TemplateProcessor):
    class xmlns(metaclass=NamespaceMeta):
        xmlns = "https://xmlns.zombofant.net/xsltea/sitemap"

    def __init__(self, name, sitemap, **kwargs):
        super().__init__(**kwargs)
        self._sitemap = sitemap
        self._name = name
        self.attrhooks = {}
        self.elemhooks = {
            (str(self.xmlns), "insert"): [self.handle_sitemap]
        }

        self._outputfmts = {
            "xml": self._xml_sitemap
        }

    def _build_xml_sitemap(self, template, elem, node):
        if node.label:
            elem.set("label", node.label)
        if node.routable:
            routable_name = template.store(node.routable)
            elem.set(xsltea.exec.ExecProcessor.xmlns.href,
                     "href(template_storage[{!r}])".format(routable_name))
            elem.set(xsltea.exec.ExecProcessor.xmlns.active,
                     "'' if request.current_routable == template_storage[{!r}] "
                     "else None".format(routable_name))
        for child in node:
            childelem = etree.SubElement(elem, self.xmlns.entry)
            self._build_xml_sitemap(template, childelem, child)

    def _xml_sitemap(self, template, elem, filename, offset):
        root = etree.Element(self.xmlns.entry)
        self._build_xml_sitemap(template, root, self._sitemap)
        return template.default_subtree(root, filename, offset)

    def handle_sitemap(self, template, elem, filename, offset):
        try:
            name = elem.attrib[self.xmlns.name]
            outputfmt = elem.attrib.get(self.xmlns.format, "xml")
        except KeyError as err:
            raise ValueError(
                "missing required attribute on tea:sitemap: @tea:{}".format(
                    str(err).split("}", 1)[1]))

        if name != self._name:
            return False

        try:
            fmt_handler = self._outputfmts[outputfmt]
        except KeyError as err:
            raise ValueError("Unknown tea:sitemap output format: {}".format(
                err))

        return fmt_handler(template, elem, filename, offset)
