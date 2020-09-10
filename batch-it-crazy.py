import json
import os
import sys
import time
import multiprocessing
from PySide2 import QtCore
from PySide2 import QtWidgets
from PySide2.QtWidgets import QApplication, QMainWindow, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit, QPushButton, QDialog, QLabel, QProgressDialog, QCheckBox, QSpinBox
from PySide2.QtCore import Slot, Signal, QObject



#interpret

interpretHelp = """Variables: line (%L), dirname (%D), basename (%B), prefix (basename w/o num/ext, %P), file number (%F), extension (%E), Line number (%N)"""



def interpret(line, cmd, lineNumber):
    locals = {"line": line,
    "dirname": os.path.dirname(line),
    "basename": os.path.basename(line),
    "prefix": ".".join(os.path.basename(line).split(".")[:max(1,len(os.path.basename(line).split("."))-1)]),
    "filenumber": "",
    "extension": line.split(".")[-1],
    "lineNumber": str(lineNumber)
    }

    while len(locals["prefix"]) and locals["prefix"][-1].isdigit():
        locals["filenumber"] = locals["prefix"][-1] + locals["filenumber"]
        locals["prefix"] = locals["prefix"][:-1]

    rets = []
    for i in cmd.split("\n"):
        i = i.replace("%L", locals["line"]).replace("%D", locals["dirname"]).replace("%F", locals["filenumber"]).replace("%B", locals["basename"]).replace("%P", locals["prefix"]).replace("%N", locals["lineNumber"]).replace("%E", locals["extension"])
        try:
            ret = eval(i,locals)
            if isinstance(ret, list):
                rets += ret
            else:
                rets.append(ret)
        except Exception as e:
            print("Error interpreting command:'''", i, "'''", e)

    return rets







#gui





class ListGroup(QVBoxLayout):
    def __init__(self, app, label, list):
        super().__init__()
        self.app = app

        self.label = QLabel(label)
        self.addWidget(self.label)

        self.list = list
        self.addWidget(self.list)

        self.button_layout = QHBoxLayout()
        self.addLayout(self.button_layout)

    def addLines(self, lines):
        widgets = []
        for i in lines:
            widget = QListWidgetItem(i)
            widgets.append(widget)
            self.list.addItem(widget)
        return widgets
        #self.list.addItems(lines)

    def getLines(self):
        ret = []
        for i in range(self.list.count()):
            ret.append(self.list.item(i).text())
        return ret

    def popLine(self):
        line = self.getLines()[0]
        self.removeLines([0])
        return line

    def removeLines(self, lines): #lines = list of line numbers
        widgets = []
        for i in lines:
            widgets.append(self.list.item(i))
        for i in widgets:
            self.removeWidget(i)

    def removeWidget(self, widget):
        row = self.list.row(widget)
        self.list.takeItem(row)
        del widget

    def removeSelectedLines(self):
        rows = []
        for i in self.list.selectedItems():
            rows.append(self.list.indexFromItem(i).row())
            #print(i)
        self.removeLines(rows)

    def removeAllLines(self):
        self.removeLines(range(self.list.count()))
        #self.list.clear()

    def getNumLines(self):
        return self.list.count()


    def paste(self):
        clipboard = QApplication.clipboard()
        lines = clipboard.text().split("\n")
        self.addLines(lines)


    def copy(self):
        clipboard = QApplication.clipboard()
        text = "\n".join(self.getLines())
        clipboard.setText(text) 
        


class LineList(QListWidget):
    def __init__(self, group, editable = False, droppable=False):
        super().__init__()
        self.group = group
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        if(editable):
            self.itemDoubleClicked.connect(self.editItem)

        if(droppable):
            self.setAcceptDrops(True)



    def editLine(self, item):
        print("todo: edit line ", item)


    def dragEnterEvent(self, e):
        print("drag enter!")
        e.accept()

    def dragMoveEvent(self, event):
        event.accept()

    def dropEvent(self, e):
        print("drop!", e)
        e.accept()

        if e.mimeData().hasUrls():
            lines = []
            for url in e.mimeData().urls():
                file_name = url.toLocalFile()
                if os.path.isdir(file_name) and not file_name.endswith("/"):
                    file_name += "/"
                lines.append(file_name)
        else:
            pass ###lines = e.gettext().split("\n")
        
        self.group.addLines(lines)










class InputGroup(ListGroup):
    def __init__(self, app):
        linelist = LineList(self, editable=True, droppable=True)
        super().__init__(app, "Input", linelist)

        self.paste_button = QPushButton("paste")
        self.button_layout.addWidget(self.paste_button)
        self.paste_button.clicked.connect(self.paste)

        self.add_button = QPushButton("add...")
        self.button_layout.addWidget(self.add_button)

        self.remove_selected_button = QPushButton("remove selected")
        self.button_layout.addWidget(self.remove_selected_button)
        self.remove_selected_button.clicked.connect(self.removeSelectedLines)

        self.remove_all_button = QPushButton("remove all")
        self.button_layout.addWidget(self.remove_all_button)
        self.remove_all_button.clicked.connect(self.removeAllLines)


    def removeLines(self, lines):
        super().removeLines(lines)
        if len(lines):
            self.app.updateOutput()

    def addLines(self, lines):
        super().addLines(lines)
        self.app.updateOutput()


class InterpretedGroup(ListGroup):
    def __init__(self, app):
        super().__init__(app, "Interpreted", LineList(self))

        self.copy_button = QPushButton("copy")
        self.button_layout.addWidget(self.copy_button)
        self.copy_button.clicked.connect(self.copy)

        self.queue_button = QPushButton("queue all")
        self.button_layout.addWidget(self.queue_button)
        self.queue_button.clicked.connect(self.queue_all)
        
        self.save_button = QPushButton("save output...")
        self.button_layout.addWidget(self.save_button)



    def queue_all(self):
        self.app.window.queue.addLines(self.getLines())






class QueueGroup(ListGroup):
    def __init__(self, app):
        super().__init__(app, "Queue", LineList(self, editable=True, droppable=True))

        self.remove_selected_button = QPushButton("remove selected")
        self.button_layout.addWidget(self.remove_selected_button)
        self.remove_selected_button.clicked.connect(self.removeSelectedLines)

        self.remove_all_button = QPushButton("remove all")
        self.button_layout.addWidget(self.remove_all_button)
        self.remove_all_button.clicked.connect(self.removeAllLines)
        
        self.paste_button = QPushButton("paste")
        self.button_layout.addWidget(self.paste_button)
        self.paste_button.clicked.connect(self.paste)






class ExecutionerGroup(ListGroup):
    def __init__(self, app):
        super().__init__(app, "Executing", LineList(self))

        self.thread_label = QLabel("Threads:")
        self.button_layout.addWidget(self.thread_label)

        self.threads_input = QSpinBox()
        self.button_layout.addWidget(self.threads_input)
        self.threads_input.setMinimum(1)
        self.threads_input.setMaximumWidth(50)
        #self.threads_input.valueChanged.connect(self.app.updateExecutionList)

        self.execute_check = QCheckBox("execute")
        self.button_layout.addWidget(self.execute_check)
        self.execute_check.stateChanged.connect(self.executeCheckChange)

    def isExecuting(self):
        return self.execute_check.isChecked()

    def executeCheckChange(self):
        #if self.execute_check.isChecked():
        #self.app.updateExecutionList()
        pass


    def getMaxThreads(self):
        return self.threads_input.value()

    def getNumThreads(self):
        return self.list.count()





class LogGroup(ListGroup):
    def __init__(self, app):
        super().__init__(app, "Log", LineList(self))
        self.copy_button = QPushButton("copy")
        self.button_layout.addWidget(self.copy_button)
        self.copy_button.clicked.connect(self.copy)

        self.clear_button = QPushButton("clear")
        self.button_layout.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.removeAllLines)


    def log(self, line):
        self.list.insertItem(0, line)



class ErrorGroup(ListGroup):
    def __init__(self, app):
        super().__init__(app, "Errors", LineList(self))
        self.copy_button = QPushButton("copy")
        self.button_layout.addWidget(self.copy_button)
        self.copy_button.clicked.connect(self.copy)

        self.clear_button = QPushButton("clear")
        self.button_layout.addWidget(self.clear_button)
        self.clear_button.clicked.connect(self.removeAllLines)


    def log(self, line):
        self.list.insertItem(0, line)




class CmdLine(QLineEdit):
    pass


class PresetDialog(QDialog):
    def __init__(self, app):
        super().__init__()
        self.app = app
        app.loadPresets()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.list = QListWidget()
        self.layout.addWidget(self.list)
        self.list.itemDoubleClicked.connect(self.load_preset)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.buttonsLayout = QHBoxLayout()
        self.layout.addLayout(self.buttonsLayout)

        self.okButton = QPushButton("OK")
        self.buttonsLayout.addWidget(self.okButton)
        self.okButton.clicked.connect(self.load_preset)

        self.cancelButton = QPushButton("Cancel")
        self.buttonsLayout.addWidget(self.cancelButton)
        self.cancelButton.clicked.connect(self.reject)

        self.load_presets()


    def load_presets(self):
        presets = []
        for i in self.app.presets:
            presets.append(i["description"] + ": " + i["preset"] + " (" + i["help"] + ")")
        self.list.addItems(presets)

    def load_preset(self):
        presetStrings = []
        helps = []
        for i in self.list.selectedItems():
            presetStrings.append(self.app.presets[self.list.indexFromItem(i).row()]["preset"])
            helps.append(self.app.presets[self.list.indexFromItem(i).row()]["help"])
        presetString = "; ".join(presetStrings)
        helpString = " ".join(helps)
        self.app.setCmdLine(presetString)
        self.app.setPresetHelp(helpString)
        #print(presetString)
        self.accept()


class BatchItWindow(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app


        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.interpret_label = QLabel("Interpret")
        self.main_layout.addWidget(self.interpret_label)

        self.help_label = QLabel(interpretHelp)
        self.main_layout.addWidget(self.help_label)

        self.cmd_layout = QHBoxLayout()
        self.main_layout.addLayout(self.cmd_layout)

        self.help2_label = QLabel()
        self.main_layout.addWidget(self.help2_label)


        self.presets_button = QPushButton("presets...")
        self.cmd_layout.addWidget(self.presets_button)
        self.presets_button.clicked.connect(self.preset_dialog)

        self.cmd_line = CmdLine('"%L"')
        self.cmd_layout.addWidget(self.cmd_line)

        self.update_button = QPushButton("update")
        self.cmd_layout.addWidget(self.update_button)
        self.update_button.clicked.connect(self.app.updateOutput)

        self.io_layout = QHBoxLayout()
        self.main_layout.addLayout(self.io_layout)

        self.input = InputGroup(self.app)
        self.io_layout.addLayout(self.input)

        self.interpreted = InterpretedGroup(self.app)
        self.io_layout.addLayout(self.interpreted)



        self.queue = QueueGroup(self.app)
        self.main_layout.addLayout(self.queue)

        self.executioner = ExecutionerGroup(self.app)
        self.main_layout.addLayout(self.executioner)



        self.log_layout = QHBoxLayout()
        self.main_layout.addLayout(self.log_layout)

        self.errors = ErrorGroup(self.app)
        self.log_layout.addLayout(self.errors)

        self.log = LogGroup(self.app)
        self.log_layout.addLayout(self.log)


        self.show()

    def preset_dialog(self):
        preDia = PresetDialog(self.app)
        preset = preDia.exec()

    def closeEvent(self, event):
        print("closing!")
        self.app.is_running = False
        event.accept()




class ExecutionWorkerSignals(QObject):
    finished = Signal()




class ExecutionWorker(QtCore.QRunnable):
    def __init__(self, app, line):
        super().__init__()
        self.app = app
        self.line = line
        self.signals = ExecutionWorkerSignals()

    @Slot()
    def run(self):
        widget = self.app.window.executioner.addLines([self.line])[0]
        try:
            
            process = multiprocessing.Process(target=workerExecutionProcess, args=(self.line,))
            process.start()
            process.join()

            
            if process.exitcode == 0:
                self.app.window.log.log(self.line)
            else:
                self.app.window.errors.log(self.line)

        except Exception as e:
            print("failed executing:", self.line)
            print(e)
            
            self.app.window.errors.log(self.line)

        self.app.window.executioner.removeWidget(widget)



class QueueWorker(QtCore.QRunnable):
    def __init__(self, app):
        super().__init__()
        self.app = app

    @Slot()
    def run(self):
        while self.app.is_running:
            self.app.updateExecutionList()
            time.sleep(.5)


def workerExecutionProcess(line):
    return os.system(line)



#app

class BatchItCrazy:
    def __init__(self):
        self.qapp = QApplication()
        
        self.window = BatchItWindow(self)
        
        self.thread_pool = QtCore.QThreadPool()

        self.is_running = True
        self.queue_worker_pool = QtCore.QThreadPool()
        self.queue_worker = QueueWorker(self)
        self.queue_worker_pool.start(self.queue_worker)


    def updateExecutionList(self):
        #print("updating execution list")
        if self.window.executioner.isExecuting() and self.thread_pool.activeThreadCount() < self.window.executioner.getMaxThreads() and self.window.queue.getNumLines():
            worker = ExecutionWorker(self, self.window.queue.popLine())
            self.thread_pool.start(worker)


    def updateOutput(self):
        cmdString = self.window.cmd_line.text()
        self.window.interpreted.removeAllLines()
        itemList = self.window.input.getLines()
        output = []
        for i in range(len(itemList)):
            for j in interpret(itemList[i], cmdString, i):
                output.append(j)
            
        self.window.interpreted.removeAllLines()
        self.window.interpreted.addLines(output)
                


    def setCmdLine(self, line):
        self.window.cmd_line.setText(line)
        self.updateOutput()


    def loadPresets(self):
        presetFiles = ["presets.json"]
        try:
            presetFile = os.environ["BATCHITCRAZY_PRESETS"].split(";")
            for i in presetFile:
                if i != "":
                    presetFiles.append(i)
        except KeyError:
            pass

        self.presets = []
        for i in presetFiles:
            try:
                for j in json.load(open(i)):
                    #if "description" in j.keys() and "preset" in j.keys() and "help" in j.keys():
                    self.presets.append(j)
            except Exception as e:
                print("ERROR reading preset file", i, ":", e)


    def setPresetHelp(self, helpString):
        self.window.help2_label.setText("preset help: " + helpString)



if __name__ == "__main__":

    

    app = BatchItCrazy()
    app.window.input.addLines(sys.argv[1:])
    sys.exit(app.qapp.exec_())
