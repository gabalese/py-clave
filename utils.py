import zipfile as ZIP
import sys
import os
try:
	from lxml import etree as ET
except:
	print("ERROR: lxml library must be installed.")
	sys.exit(1)

namespaces = {"opf":"http://www.idpf.org/2007/opf","dc":"http://purl.org/dc/elements/1.1/"}

class Metadata:
	def __init__(self, file):
		opf = self.parseOPF(file)
		
		self.title = opf.xpath("//dc:title",namespaces=namespaces)[0].text
		self.author = opf.xpath("//dc:creator",namespaces=namespaces)[0].text
		self.isbn = opf.xpath("//dc:identifier",namespaces=namespaces)[0].text
		self.language = opf.xpath("//dc:language",namespaces=namespaces)[0].text
		self.publisher = opf.xpath("//dc:publisher",namespaces=namespaces)[0].text
		self.pubdate = opf.xpath("//dc:date[@opf:event='publication']",namespaces=namespaces)[0]
		
	def parseInfo(self, file):
		info = {}
		try:
			f = ZIP.ZipFile(file).read("META-INF/container.xml")
		except KeyError:
			print  "The %s file is not a valid OCF." % str(file)
		try:
			f = ET.fromstring(f)
			info["path_to_opf"] = f[0][0].get("full-path")
			root_folder = os.path.dirname(info["path_to_opf"])
		except:
			pass
		opf = ET.fromstring(ZIP.ZipFile(file).read(info["path_to_opf"]))
	
		id = opf.xpath("//opf:spine",namespaces=namespaces)[0].get("toc")
		expr = "//*[@id='%s']" % id
		info["ncx_name"] = opf.xpath(expr)[0].get("href")
		info["path_to_ncx"] = root_folder + "/" + info["ncx_name"]
		info.pop("ncx_name")

		return info
	
	def parseOPF(self, file):
		meta = {}
		opf = ET.fromstring(ZIP.ZipFile(file).read(self.parseInfo(file)["path_to_opf"]))
	
		return opf
	
	def parseNCX(self, file):

		ncx = {}
		ncx = ET.fromstring(ZIP.ZipFile(file).read(self.parseInfo(file)["path_to_ncx"]))
	
		return ncx