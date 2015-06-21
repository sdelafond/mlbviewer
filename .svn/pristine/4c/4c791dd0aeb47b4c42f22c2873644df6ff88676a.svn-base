#!/usr/bin/env python

from xml.dom import *
from xml.dom.minidom import *
import sys

try:
  xmlfile = sys.argv[1]
except:
  print "%s: Please specify an xml filename to parse" % sys.argv[0]
  sys.exit()

try:
  xp = parse(xmlfile)
except:
  print "%s %s: Could not parse xmlfile." % (sys.argv[0], xmlfile)
  sys.exit()

IL = 0

def printChildNodes(node,IL):
  if node.hasChildNodes():
    print "%s %s:" % (IL*' ', node.nodeName)
    if node.nodeType in ( node.ELEMENT_NODE , ):
      printNodeAttributes(node,IL)
    IL += 1
    for child in node.childNodes:
      printChildNodes(child,IL)
  else:
    print "%s %s: %s" % (IL*' ', node.nodeName, node.nodeValue)
    if node.nodeType in ( node.ELEMENT_NODE , ):
      printNodeAttributes(node,IL)
    IL -= 1

def printNodeAttributes(node,IL):
    if node.hasAttributes():
      IL+=1
      for n in range(node.attributes.length):
        #print "%s %s:" % (IL*' ', str(node.attributes.item(n).nodeValue))
        print "%s %s: %s" % (IL*' ', str(node.attributes.item(n).nodeName),
                                     str(node.attributes.item(n).nodeValue))
    IL -=1

printChildNodes(xp,IL)
