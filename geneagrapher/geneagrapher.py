# $License$

from optparse import OptionParser
import GGraph
import grab

class Geneagrapher:
	"""
	A class for building Graphviz "dot" files for math genealogies
	extracted from the Mathematics Genealogy Project website.
	"""
	def __init__(self):
		self.graph = GGraph.Graph()
		self.leaf_ids = []
		self.get_ancestors = False
		self.get_descendents = False
		self.verbose = False
		self.supp_node_filename = None
		self.write_filename = None

	def parseInput(self):
		"""
		Parse command-line information.
		"""
		self.parser = OptionParser()

		self.parser.set_usage("%prog [options] ID ...")
		self.parser.set_description('Create a Graphviz "dot" file for a mathematics genealogy, where ID is a record identifier from the Mathematics Genealogy Project. Multiple IDs may be passed.')

		self.parser.add_option("-f", "--file", dest="filename",
				       help="write report to FILE [default: stdout]", metavar="FILE", default=None)
		self.parser.add_option("-a", "--with-ancestors", action="store_true", dest="get_ancestors",
				       default=False, help="do not get ancestors of any input IDs")
		self.parser.add_option("-d", "--with-descendents", action="store_true", dest="get_descendents",
				       default=False, help="do not get ancestors of any input IDs")
		self.parser.add_option("--verbose", "-v", action="store_true", dest="verbose", default=False,
				       help="print information showing progress")
		self.parser.add_option("--version", "-V", action="store_true", dest="print_version", default=False,
				       help="print geneagrapher version and exit")
		self.parser.add_option("-n", "--attach-node-file", dest="supp_node_filename", metavar="FILE",
				       help="attach supplementary nodes returned by function 'define_supp_nodes()' in FILE to the graph", default=None)

		(options, args) = self.parser.parse_args()
		
		if options.print_version:
			print "Geneagrapher Version 0.2"
			self.parser.exit()
		
		if len(args) == 0:
			raise SyntaxError("%s: error: no record IDs passed" % (self.parser.get_prog_name()))

		self.get_ancestors = options.get_ancestors
		self.get_descendents = options.get_descendents
		self.verbose = options.verbose
		self.supp_node_filename = options.supp_node_filename
		self.write_filename = options.filename
		for arg in args:
			self.leaf_ids.append(int(arg))
		
	def buildGraph(self):
		"""
		Populate the graph member by grabbing the mathematician
		pages and extracting relevant data.
		"""
		leaf_grab_queue = list(self.leaf_ids)
		ancestor_grab_queue = []
		descendent_grab_queue = []

		# Grab "supplementary" nodes from file.
		if self.supp_node_filename is not None:
			supp_node_modname = self.supp_node_filename.split('.')[0]
			importstr = "import %s" % (supp_node_modname)
			exec(importstr)
			if "define_supp_nodes" not in dir(eval(supp_node_modname)):
				errstr = "'%s' module has no function 'define_supp_nodes'" % (supp_node_modname)
				raise AttributeError(errstr)
			supp_nodes = eval(supp_node_modname).define_supp_nodes()
			for node in supp_nodes:
				self.graph.addNodeObject(node, True)
		
		# Grab "leaf" nodes.
		while len(leaf_grab_queue) != 0:
			id = leaf_grab_queue.pop()
			if not self.graph.hasNode(id):
				# Then this information has not yet been grabbed.
				grabber = grab.Grabber(id)
				if self.verbose:
					print "Grabbing record #%d" % (id)
				try:
					[name, institution, year, advisors, descendents] = grabber.extractNodeInformation()
				except ValueError:
					# The given id does not exist in the Math Genealogy Project's database.
					raise
				self.graph.addNode(name, institution, year, id, advisors, descendents, True)
				if self.get_ancestors:
					ancestor_grab_queue += advisors
				if self.get_descendents:
					descendent_grab_queue += descendents

		# Grab ancestors of leaf nodes.
		if self.get_ancestors:
			while len(ancestor_grab_queue) != 0:
				id = ancestor_grab_queue.pop()
				if not self.graph.hasNode(id):
					# Then this information has not yet been grabbed.
					grabber = grab.Grabber(id)
					if self.verbose:
						print "Grabbing record #%d" % (id)
					try:
						[name, institution, year, advisors, descendents] = grabber.extractNodeInformation()
					except ValueError:
						# The given id does not exist in the Math Genealogy Project's database.
						raise
					self.graph.addNode(name, institution, year, id, advisors, descendents)
					ancestor_grab_queue += advisors
						
		# Grab descendents of leaf nodes.
		if self.get_descendents:
			while len(descendent_grab_queue) != 0:
				id = descendent_grab_queue.pop()
				if not self.graph.hasNode(id):
					# Then this information has not yet been grabbed.
					grabber = grab.Grabber(id)
					if self.verbose:
						print "Grabbing record #%d" % (id)
					try:
						[name, institution, year, advisors, descendents] = grabber.extractNodeInformation()
					except ValueError:
						# The given id does not exist in the Math Genealogy Project's database.
						raise
					self.graph.addNode(name, institution, year, id, advisors, descendents)
					descendent_grab_queue += descendents
					
	def generateDotFile(self):
		dotfile = self.graph.generateDotFile(self.get_ancestors, self.get_descendents)
		if self.write_filename is not None:
			outfile = open(self.write_filename, "w")
			outfile.write(dotfile)
			outfile.close()
		else:
			print dotfile
		
if __name__ == "__main__":
	geneagrapher = Geneagrapher()
	try:
		geneagrapher.parseInput()
	except SyntaxError, e:
		print geneagrapher.parser.get_usage()
		print e
	geneagrapher.buildGraph()
	geneagrapher.generateDotFile()