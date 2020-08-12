import ctypes
from PySide2.QtCore import Signal, Slot, Property, QObject, QSize
from PySide2.QtQuick import QQuickItem, QQuickWindow
from PySide2.QtCore import Qt
from PySide2.QtGui import QOpenGLShader, QOpenGLShaderProgram
import numpy as np
from OpenGL.GL import *


class SquircleRenderer(QObject):
    def __init__ ( self, parent = None ):
        super().__init__(parent)
        self._shader_program = None
        self._t = 0.0
        self._viewport_size = QSize()
        self._window = None

    def set_viewport_size ( self, viewport_size ):
        self._viewport_size = viewport_size

    def set_t (self, t):
        self._t = t

    def set_window ( self, window ):
        self._window = window

    @Slot()
    def paint(self):
        try:
            print("drawing({})".format(self._t))
            if self._shader_program is None:
                self._shader_program = QOpenGLShaderProgram()
                self._shader_program.addShaderFromSourceFile(QOpenGLShader.Vertex, 'shaders/vertex.glsl')
                self._shader_program.addShaderFromSourceFile(QOpenGLShader.Fragment, 'shaders/fragment.glsl')
                self._shader_program.bindAttributeLocation('vertices', 0)
                self._shader_program.link()

            self._shader_program.bind()
            self._shader_program.enableAttributeArray(0)

            x0, x1 = (-1.0, 1.0)
            y0, y1 = (-1.0, 1.0)
            values = np.array([ (x0, y0), (x1, y0), (x0, y1), (x1, y1) ], dtype=ctypes.c_float)

            self._shader_program.setAttributeArray(0, GL_FLOAT, values.tobytes(), 2)
            self._shader_program.setUniformValue(0, self._t)

            gl = self._window.openglContext().functions()
            gl.glViewport(0, 0, self._viewport_size.width(), self._viewport_size.height())

            gl.glDisable(GL_DEPTH_TEST)

            gl.glClearColor(0.1, 0.1, 0.1, 1)
            gl.glClear(GL_COLOR_BUFFER_BIT)

            gl.glEnable(GL_BLEND)
            gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE)

            gl.glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
            self._shader_program.disableAttributeArray(0)
            self._shader_program.release()

            self._window.resetOpenGLState()
        except Exception as e:
            print(e)


class Squircle(QQuickItem):
    def __init__ ( self, t = 0.0, parent = None ):
        super().__init__(parent)
        # self._renderer = None
        self._t = t
        self._renderer = None
        self.windowChanged.connect(self.onWindowChanged)

    @Slot(QQuickWindow)
    def onWindowChanged ( self, window ):
        self.window().beforeSynchronizing.connect(self.sync, type = Qt.DirectConnection)
        self.window().setClearBeforeRendering(False)

    @Slot()
    def sync ( self ):
        print("sync({})".format(self._t))
        if self._renderer is None:
            self._renderer = SquircleRenderer()
            self.window().beforeRendering.connect(self._renderer.paint, type = Qt.DirectConnection)
        self._renderer.set_viewport_size(self.window().size() * self.window().devicePixelRatio())
        self._renderer.set_t(self._t)
        self._renderer.set_window(self.window())

    def getT ( self ):
        return self._t

    def setT ( self, t ):
        if t == self._t:
            return
        self._t = t
        #print("setT({})".format(t))

        if self.window():
            self.window().update()

    @Signal
    def t_changed(self):
        pass

    t = Property(float, getT, setT, notify=t_changed)
