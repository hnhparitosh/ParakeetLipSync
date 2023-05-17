import sys
from PySide6.QtWidgets import QApplication
from LipsyncFrame import LipsyncFrame

app = QApplication(sys.argv)

window = LipsyncFrame()
window.show()

# start the event loop
app.exec()