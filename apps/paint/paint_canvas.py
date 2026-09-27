from collections import deque
from PyQt6.QtWidgets import QWidget, QInputDialog
from PyQt6.QtGui import QPainter, QPen, QColor, QImage, QPainterPath, QFont
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal

class PaintCanvas(QWidget):
    """Nyebralti Paint - Çizim Tuvali"""
    canvas_modified = pyqtSignal()

    def __init__(self, width: int = 1200, height: int = 800, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)

        # Temel görüntü ve arkaplan
        self.image = QImage(self.size(), QImage.Format.Format_RGB32)
        self.image.fill(Qt.GlobalColor.white)

        # Araç ve stil durumları
        self.current_tool = "pen"  # 'pen', 'brush', 'eraser', 'line', 'rect', 'ellipse', 'fill', 'text'
        self.pen_color = QColor(Qt.GlobalColor.black)
        self.pen_size = 3
        self.drawing = False
        self.last_point = QPoint()
        self.start_point = QPoint()

        # Geçici çizim için kopya
        self.temp_image = None

        # Undo / Redo Geçmişi
        self.undo_stack = deque(maxlen=20)
        self.redo_stack = deque(maxlen=20)
        self._push_undo()

    def _push_undo(self):
        self.undo_stack.append(self.image.copy())
        self.redo_stack.clear()
        self.canvas_modified.emit()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.image = self.undo_stack[-1].copy()
            self.update()
            self.canvas_modified.emit()

    def redo(self):
        if self.redo_stack:
            img = self.redo_stack.pop()
            self.undo_stack.append(img)
            self.image = img.copy()
            self.update()
            self.canvas_modified.emit()

    def clear(self):
        self.image.fill(Qt.GlobalColor.white)
        self._push_undo()
        self.update()

    def set_tool(self, tool_name: str):
        self.current_tool = tool_name

    def set_pen_color(self, color: QColor):
        self.pen_color = color

    def set_pen_size(self, size: int):
        self.pen_size = max(1, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.drawing and self.temp_image:
            painter.drawImage(0, 0, self.temp_image)
        else:
            painter.drawImage(0, 0, self.image)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.position().toPoint()
            self.start_point = event.position().toPoint()

            if self.current_tool in ["pen", "brush", "eraser"]:
                self._draw_stroke(self.last_point, self.last_point)
            elif self.current_tool == "fill":
                self._flood_fill(self.start_point, self.pen_color)
                self.drawing = False
                self._push_undo()
            elif self.current_tool == "text":
                self.drawing = False
                self._insert_text(self.start_point)
            else:
                self.temp_image = self.image.copy()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drawing:
            curr_point = event.position().toPoint()

            if self.current_tool in ["pen", "brush", "eraser"]:
                self._draw_stroke(self.last_point, curr_point)
                self.last_point = curr_point
            elif self.current_tool in ["line", "rect", "ellipse"]:
                self.temp_image = self.image.copy()
                painter = QPainter(self.temp_image)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(QPen(self.pen_color, self.pen_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))

                if self.current_tool == "line":
                    painter.drawLine(self.start_point, curr_point)
                elif self.current_tool == "rect":
                    rect = QRect(self.start_point, curr_point).normalized()
                    painter.drawRect(rect)
                elif self.current_tool == "ellipse":
                    rect = QRect(self.start_point, curr_point).normalized()
                    painter.drawEllipse(rect)

                painter.end()
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if self.current_tool in ["line", "rect", "ellipse"] and self.temp_image:
                self.image = self.temp_image
                self.temp_image = None

            self._push_undo()
            self.update()

    def _draw_stroke(self, start: QPoint, end: QPoint):
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = Qt.GlobalColor.white if self.current_tool == "eraser" else self.pen_color
        size = self.pen_size * 2 if self.current_tool == "eraser" else (self.pen_size * 2 if self.current_tool == "brush" else self.pen_size)

        pen = QPen(color, size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(start, end)
        painter.end()
        self.update()

    def _insert_text(self, pt: QPoint):
        text, ok = QInputDialog.getText(self, "Metin Ekle", "Çizime eklenecek metin:")
        if ok and text:
            painter = QPainter(self.image)
            painter.setPen(self.pen_color)
            painter.setFont(QFont("Segoe UI", self.pen_size * 4))
            painter.drawText(pt, text)
            painter.end()
            self._push_undo()
            self.update()

    def _flood_fill(self, pt: QPoint, fill_color: QColor):
        """Basit ve hızlı BFS Flood Fill"""
        w, h = self.image.width(), self.image.height()
        x, y = pt.x(), pt.y()
        if x < 0 or x >= w or y < 0 or y >= h:
            return

        target_rgba = self.image.pixel(x, y)
        fill_rgba = fill_color.rgba()
        if target_rgba == fill_rgba:
            return

        queue = deque([(x, y)])
        visited = set([(x, y)])

        while queue:
            cx, cy = queue.popleft()
            if self.image.pixel(cx, cy) == target_rgba:
                self.image.setPixel(cx, cy, fill_rgba)

                for nx, ny in [(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)]:
                    if 0 <= nx < w and 0 <= ny < h:
                        if (nx, ny) not in visited and self.image.pixel(nx, ny) == target_rgba:
                            visited.add((nx, ny))
                            queue.append((nx, ny))

        self.update()
