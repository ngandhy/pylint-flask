'''pylint_flask module'''

from astroid import MANAGER
from astroid.builder import AstroidBuilder
from astroid import nodes
import re
import textwrap


def register(_):
    '''register is expected by pylint for plugins, but we are creating a transform,
     not registering a checker.

    '''
    pass


def copy_node_info(src, dest):
    """Copy information from src to dest

    Every node in the AST has to have line number information.  Get
    the information from the old stmt."""
    for attr in ['lineno', 'fromlineno', 'tolineno',
                 'col_offset', 'parent']:
        if hasattr(src, attr):
            setattr(dest, attr, getattr(src, attr))


def mark_transformed(node):
    '''Mark a node as transformed so we don't process it multiple times.'''
    node.pylint_flask_was_transformed = True

def is_transformed(node):
    '''Return True if `node` was already transformed.'''
    return getattr(node, 'pylint_flask_was_transformed', False)


def transform_flask_from_import(node):
    '''Translates a flask.ext from-style import into a non-magical import.

    Translates:
        from flask.ext import wtf, bcrypt as fcrypt
    Into:
        import flask_wtf as wtf, flask_bcrypt as fcrypt

    '''
    new_names = []
    for (name, as_name) in node.names:
        actual_module_name = 'flask_{}'.format(name)
        new_names.append((actual_module_name, as_name or name))

    new_node = nodes.Import()
    copy_node_info(node, new_node)
    new_node.names = new_names
    mark_transformed(new_node)
    return new_node


def is_flask_from_import(node):
    '''Predicate for checking if we have the flask module.'''
    # Check for transformation first so we don't double process
    return not is_transformed(node) and node.modname == 'flask.ext'


def transform_flask_from_import_long(node):
    '''Translates a flask.ext.wtf from-style import into a non-magical import.

    Translates:
        from flask.ext.wtf import Form
        from flask.ext.admin.model import InlineFormAdmin
    Into:
        from flask_wtf import Form
        from flask_admin.model import InlineFormAdmin

    '''
    match = re.match('flask\.ext\.(.*)', node.modname)
    from_name = match.group(1)
    actual_module_name = 'flask_{}'.format(from_name)
    new_node = nodes.From(actual_module_name, node.names, node.level)
    copy_node_info(node, new_node)
    mark_transformed(new_node)
    return new_node


def is_flask_from_import_long(node):
    '''Check if an import is like `from flask.ext.wtf import Form`.'''
    # Check for transformation first so we don't double process
    return not is_transformed(node) and node.modname.startswith('flask.ext.')

MANAGER.register_transform(nodes.From,
                           transform_flask_from_import,
                           is_flask_from_import)

MANAGER.register_transform(nodes.From,
                           transform_flask_from_import_long,
                           is_flask_from_import_long)
