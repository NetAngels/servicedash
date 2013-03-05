#!/usr/bin/env python
#  -*- coding: utf8 -*-

from flask import Flask, url_for, render_template, redirect, request, Response
from flask.ext.bootstrap import Bootstrap
from yaml import load
from string import Template
from ReverseProxied import ReverseProxied
import os.path, time
import urllib
import ConfigParser

app = Flask(__name__)
app.wsgi_app = ReverseProxied(app.wsgi_app)
Bootstrap(app)
appconfig = ConfigParser.ConfigParser()
appconfig.read('./conf/servicedash.conf')

VERSION = '0.0.2'
CONFIGFILE = './conf/config.yaml'
config = None
config_mod_time = None

app.config['BOOTSTRAP_USE_MINIFIED'] = True
app.config['BOOTSTRAP_USE_CDN'] = True


def get_config_mod_time():
    return time.ctime(os.path.getmtime(CONFIGFILE))


def build_graphs_sublist(graphs, node):
    graphs_list = []
    for graph_str in graphs:
        t = Template(graph_str)
        graph = t.safe_substitute(**node)
        graphs_list.append(graph)
    return graphs_list


def build_tables_sublist(tables, node):
    tables_list = []
    for table_str in tables:
        t_url = Template(table_str['url'])
        url = t_url.safe_substitute(**node)
        t_title = Template(table_str['title'])
        title = t_title.safe_substitute(**node)
        tables_list.append({'title': title, 'url': url})
    return tables_list


def get_node_name(node):
    if node.__class__ == str:
        return node
    else:
        return [key for key, value in node.iteritems() if value == None][0] 


@app.before_request
def check_config():
    global config
    global config_mod_time
    if get_config_mod_time() != config_mod_time:
        config = load(open(CONFIGFILE))
        config_mod_time = get_config_mod_time()
        app.logger.debug('Config (re-)loaded')


@app.route('/render/')
def render():
    # proxy requests to graphite server from localhost
    # this code is for debug server only. it never runs in production.
    resp = urllib.urlopen(request.url.replace(request.url_root, appconfig.get('graphite', 'renderurl')))
    return Response(content_type=resp.headers.typeheader, response=resp.read())


@app.route('/')
def index():
    # show first category's first node by default
    return redirect(request.url_root + config.keys()[0] + '/' + get_node_name(config[config.keys()[0]]['nodes'][0]) + '/')


@app.route('/<current_category>/')
def show_category(current_category):
    if config.has_key(current_category):
        first_node = config[current_category]['nodes'][0]
        return redirect(request.url_root + current_category + '/' + get_node_name(first_node) + '/')
    else:
        return redirect(request.url_root)


@app.route('/<current_category>/<current_node>/')
def show_node(current_category, current_node):
    categories = []
    nodes = []
    node_dict = {'name': current_node}
    for category in config.keys():
        cat_dict = {'name': category, 'url': request.url_root + category + '/'}
        categories.append(cat_dict)
        if category == current_category:
            for n in config[category]['nodes']:
                if n.__class__ == str:
                    node = {'name': n}
                    if n == current_node:
                        node_dict['graphs'] = []
                        node_dict['tables'] = []
                else:
                    node = {'name': [key for key, value in n.iteritems() if value == None][0]}
                    if node['name'] == current_node:
                        node_dict['graphs'] = build_graphs_sublist(n['graphs'], node)
                        if n.has_key('tables'):
                            node_dict['tables'] = build_tables_sublist(n['tables'], node) 
                        if n.has_key('description'):
                            node_dict['description'] = n['description']
                if node['name'] != 'summary' and node['name'] == current_node:
                    node_dict['graphs'] = build_graphs_sublist(config[category]['graphs'], node) + node_dict['graphs']
                    if config[category].has_key('tables'):
                        node_dict['tables'] = build_tables_sublist(config[category]['tables'], node) + node_dict['tables']
                node['url'] = request.url_root + current_category + '/' + node['name'] + '/'
                nodes.append(node)

    return render_template('index.html', categories=categories, nodes=nodes, current_category=current_category, current_node=current_node, \
            node=node_dict)


if '__main__' == __name__:
    app.run(port=5012, debug=True)
