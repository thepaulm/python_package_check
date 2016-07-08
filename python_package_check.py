#!/usr/bin/env python

import glob
import re
import sys
import string
import argparse
from pkg_resources import parse_version

dist_glob_ending = '/*.dist-info'
egg_glob_ending = '/*.egg-info'


nre = re.compile("^Name: (\S*)")
vre = re.compile("^Version: (\S*)")
rre = re.compile("^Requires-Dist:\s*(\S.*)$")


class Dep(object):
    def __init__(self, name, constraint=None):
        self.name = name
        self.constraint = constraint

    def __str__(self):
        return "{%s: %s}" % (self.name, self.constraint)


class Package(object):
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.deps = {}

    def add_dep(self, dep):
        self.deps[dep.name] = dep

    def __str__(self):
        return ("%s:[%s]" % (self.name, self.version)) + string.join([str(d) for d in self.deps.itervalues()])


def parse_constraint_parts(c):
    comparitors = '!=<>'
    comp = ''
    i = 0
    for i in range(0, len(c)):
        if c[i] in comparitors:
            comp += c[i]
        else:
            break
    totest = c[i:]
    return comp, totest


def run_comparison(inst, straint, comp):
    if comp == '==':
        return parse_version(inst) == parse_version(straint)
    if comp == "<=":
        return parse_version(inst) <= parse_version(straint)
    if comp == ">=":
        return parse_version(inst) >= parse_version(straint)
    if comp == "!=":
        return parse_version(inst) != parse_version(straint)
    if comp == ">":
        return parse_version(inst) > parse_version(straint)
    if comp == "<":
        return parse_version(inst) < parse_version(straint)

    return False


def constraint_compare(inst, constraint):

    for c in constraint:
        comp, straint = parse_constraint_parts(c)
        if not run_comparison(inst, straint, comp):
            return False
    return True


def get_dist_infos(glob_search_base):
    return glob.glob(glob_search_base + dist_glob_ending)


def get_egg_infos(glob_search_base):
    return glob.glob(glob_search_base + egg_glob_ending)


def parse_constraint(sv):
    sv = sv.rstrip(')')
    sv = sv.lstrip('(')
    sv = sv.split(',')
    return sv


def parse_requires(r):
    r = r.split(';')[0]
    r = r.split()
    if len(r) > 2:
        rest = string.join(r[1:], '')
    elif len(r) > 1:
        rest = r[1]
    else:
        rest = None

    name = r[0]
    constraint = None
    if rest:
        constraint = parse_constraint(rest)

    return Dep(name, constraint)


def parse_METADATA(d):
    try:
        f = open(d + "/METADATA")
    except:
        return
    name = None
    version = None
    package = None
    for l in f:
        m = nre.match(l)
        if m:
            name = m.group(1)
        m = vre.match(l)
        if m:
            version = m.group(1)
        m = rre.match(l)
        if m:
            package.add_dep(parse_requires(m.group(1)))

        if name and version and not package:
            package = Package(name, version)
    return package


def parse_EGG(d):
    try:
        f = open(d + "/PKG-INFO")
    except:
        return
    name = None
    version = None
    package = None
    for l in f:
        m = nre.match(l)
        if m:
            name = m.group(1)
        m = vre.match(l)
        if m:
            version = m.group(1)
        if name and version:
            package = Package(name, version)
            break
    if not package:
        return

    try:
        f = open(d + "/requires.txt")
    except:
        return None
    for l in f:
        m = rre.match(l)
        if m:
            package.add_dep(parse_requires(m.group(1)))

    return package


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--package-path",
                        help="path to packages install dir (eg. site-packages). Default is "
                              "all in sys.path")
    parser.add_argument("-e", "--exclude-requires-from",
                        help="comma seperated exclude list requirements from these packages")
    return parser.parse_args()


def main():

    retval = 0
    args = get_args()

    if args.package_path:
        paths = [args.package_path]
    else:
        paths = sys.path

    excludes = []
    if args.exclude_requires_from:
        excludes = args.exclude_requires_from.split(',')

    packages = {}

    for glob_search_base in paths:
        dist_infos = get_dist_infos(glob_search_base)
        for d in dist_infos:
            p = parse_METADATA(d)
            if p:
                packages[p.name] = p

        egg_infos = get_egg_infos(glob_search_base)
        for e in egg_infos:
            p = parse_EGG(e)
            if p:
                packages[p.name] = p

    for p in packages.itervalues():
        for p2 in packages.itervalues():
            if p.name in p2.deps and p2.deps[p.name].constraint is not None:
                if not constraint_compare(p.version, p2.deps[p.name].constraint) and \
                   p2.name not in excludes:
                    retval = -1
                    print "FAILED: %s ver %s installed, %s ver %s requires %s" % \
                          (p.name, p.version, p2.name, p2.version, p2.deps[p.name].constraint)
                    for p3 in packages.itervalues():
                        if p3 != p2 and p.name in p3.deps:
                            other = p3.deps[p.name].constraint
                            if other is None:
                                other = "any"
                            print "\talso from: %s ver %s requiring %s" % (p3.name, p3.version, other)
    sys.exit(retval)


if __name__ == '__main__':
    main()
