#!/usr/bin/env python
# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
## Contact: http://www.qt-project.org/legal
##
## This file is part of the test suite of the Qt Toolkit.
##
## $QT_BEGIN_LICENSE:LGPL$
## Commercial License Usage
## Licensees holding valid commercial Qt licenses may use this file in
## accordance with the commercial license agreement provided with the
## Software or, alternatively, in accordance with the terms contained in
## a written agreement between you and Digia.  For licensing terms and
## conditions see http://qt.digia.com/licensing.  For further information
## use the contact form at http://qt.digia.com/contact-us.
##
## GNU Lesser General Public License Usage
## Alternatively, this file may be used under the terms of the GNU Lesser
## General Public License version 2.1 as published by the Free Software
## Foundation and appearing in the file LICENSE.LGPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU Lesser General Public License version 2.1 requirements
## will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
##
## In addition, as a special exception, Digia gives you certain additional
## rights.  These rights are described in the Digia Qt LGPL Exception
## version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
##
## GNU General Public License Usage
## Alternatively, this file may be used under the terms of the GNU
## General Public License version 3.0 as published by the Free Software
## Foundation and appearing in the file LICENSE.GPL included in the
## packaging of this file.  Please review the following information to
## ensure the GNU General Public License version 3.0 requirements will be
## met: http://www.gnu.org/copyleft/gpl.html.
##
##
## $QT_END_LICENSE$
##
#############################################################################

from __future__ import with_statement
from string import Template

class Options():
  """Option manager. It parse and check all paramteres, set internal variables."""
  def __init__(self, args):
    import logging as log
    log.basicConfig()
    #comand line options parser
    from optparse import OptionParser
    #load some directory searching stuff
    import os.path, sys
      
    opt = OptionParser("%prog [options] path_to_input_file path_to_output_file.")
    
    self._o, self._a = opt.parse_args(args)

    try:
      if not (os.path.exists(self._a[0])):
        raise Exception("Path doesn't exist")
      if len(self._a) != 2:
        raise IndexError("Only two files!")
      self._o.ipath = self._a[0]
      self._o.opath = self._a[1]
    except IndexError:
      log.error("Bad usage. Please try -h or --help")
      sys.exit(1)
    except Exception:
      log.error("Path '" + self._a[0] + " or " + self._a[1] + "' don't exist")
      sys.exit(2)

  def __getattr__(self, attr):
    """map all options properties into this object (remove one level of indirection)"""
    return getattr(self._o, attr)


mainTempl = Template("""/****************************************************************************
**
** Copyright (C) 2013 Digia Plc and/or its subsidiary(-ies).
** Contact: http://www.qt-project.org/legal
**
** This file is part of the test suite of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:LGPL$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and Digia.  For licensing terms and
** conditions see http://qt.digia.com/licensing.  For further information
** use the contact form at http://qt.digia.com/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 2.1 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU Lesser General Public License version 2.1 requirements
** will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** In addition, as a special exception, Digia gives you certain additional
** rights.  These rights are described in the Digia Qt LGPL Exception
** version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 3.0 as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU General Public License version 3.0 requirements will be
** met: http://www.gnu.org/copyleft/gpl.html.
**
**
** $QT_END_LICENSE$
**
****************************************************************************/

////////////////////////////////////////////////////////////////
// THIS FILE IS AUTOGENERATED, ALL MODIFICATIONS WILL BE LAST //
////////////////////////////////////////////////////////////////

#include "testgenerator.h"

#include <QtCore/qdatastream.h>
#include <QtCore/qdatetime.h>
#include <QtCore/qdebug.h>
#include <QtCore/qfile.h>
#include <QtCore/qnumeric.h>
#include <QtCore/qvariant.h>
#include <QtCore/qvector.h>
#include <QtScript/qscriptvalue.h>
#include <QtScript/qscriptengine.h>



typedef bool (QScriptValue::*ComparisionType) (const QScriptValue&) const;
static QVector<bool> compare(ComparisionType compare, QScriptValue value, const QScriptValueList& values) {
    QVector<bool> result;
    result.reserve(${count});

    QScriptValueList::const_iterator i = values.constBegin();
    for (; i != values.constEnd(); ++i) {
        result << (value.*compare)(*i);
    }
    return result;
}

static void dump(QDataStream& out, QScriptValue& value, const QString& expression, const QScriptValueList& allValues)
{
        out << QString(expression);
        
        out << value.isValid();
        out << value.isBool();
        out << value.isBoolean();
        out << value.isNumber();
        out << value.isFunction();
        out << value.isNull();
        out << value.isString();
        out << value.isUndefined();
        out << value.isVariant();
        out << value.isQObject();
        out << value.isQMetaObject();
        out << value.isObject();
        out << value.isDate();
        out << value.isRegExp();
        out << value.isArray();
        out << value.isError();

        out << value.toString();
        out << value.toNumber();
        out << value.toBool();
        out << value.toBoolean();
        out << value.toInteger();
        out << value.toInt32();
        out << value.toUInt32();
        out << value.toUInt16();

        out << compare(&QScriptValue::equals, value, allValues);
        out << compare(&QScriptValue::strictlyEquals, value, allValues);
        out << compare(&QScriptValue::lessThan, value, allValues);
        out << compare(&QScriptValue::instanceOf, value, allValues);

        out << qscriptvalue_cast<QString>(value);
        out << qscriptvalue_cast<qsreal>(value);
        out << qscriptvalue_cast<bool>(value);
        out << qscriptvalue_cast<qint32>(value);
        out << qscriptvalue_cast<quint32>(value);
        out << qscriptvalue_cast<quint16>(value);
}

void TestGenerator::prepareData()
{
    QScriptEngine* engine = new QScriptEngine;

    QScriptValueList allValues;
    allValues << ${values};
    QVector<QString> allDataTags;
    allDataTags.reserve(${count});
    allDataTags << ${dataTags};
    QDataStream out(&m_tempFile);
    out << allDataTags;

    for(unsigned i = 0; i < ${count}; ++i)
      dump(out, allValues[i], allDataTags[i], allValues);

    delete engine;
}
""")
qsvTempl = Template("""
    {
        QScriptValue value = ${expr};
        dump(out, value, "${expr_esc}", allValues);
    }""")



if __name__ == '__main__':
  import sys
  o = Options(sys.argv[1:])
  out = []
  qsv = []
  # load input file
  with open(o.ipath) as f:
    for row in f.readlines():
      qsv.append(row)

  #skip comments and empty lines
  qsv = filter(lambda w: len(w.strip()) and not w.startswith('#'), qsv)
  
  escape = lambda w: w.replace('\\','\\\\').replace('"','\\"')
  
  for row in qsv:
    row = row.replace('\n','')
    row_esc = escape(row)
    out.append(qsvTempl.substitute(expr = row, expr_esc = row_esc))

  result = mainTempl.safe_substitute(dump= "".join(out) \
                              , values = (11 * ' ' + '<< ').join(qsv) \
                              , count = len(qsv) \
                              , dataTags = (11 * ' ' + '<< ').join(map(lambda w: '"' + escape(w.replace('\n','')) + '"\n', qsv)))

  with open(o.opath, 'w') as f:
    f.write(result)

  
