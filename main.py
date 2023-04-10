import sys
from PySide6.QtWidgets import QApplication
from LipsyncFrame import LipsyncFame

app = QApplication(sys.argv)

window = LipsyncFame()
window.show()

# start the event loop
app.exec()