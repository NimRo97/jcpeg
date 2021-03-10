import os

from jcpeg.config import Paths
from jcpeg.interfaces import Module, ToolWrapper
from jcpeg.utils import execute_cmd, isfile

class JCAlgTest(ToolWrapper):

    BIN = "java -jar " + Paths.JCALGTEST
    CAPS = Paths.JCALGTEST_CAPS

    def __init__(self, card_name, force_mode=False, install=True):
        super().__init__(card_name, force_mode)

        if install:
            self.install()
            
        self.support_file = None
        self.performance_file = None
        self.variable_file = None

    def install(self):
        for applet in Paths.JCALGTEST_CAPS:
            cmd_line = "java -jar bin/gp.jar -install " + applet
            if execute_cmd(cmd_line) == 0:
                break

    def is_support_file(self):
        if self.support_file:
            return self.support_file
        for file in os.listdir("results/" + self.card_name):
            if "ALGSUPPORT" in file:
                self.support_file = file
        return self.support_file
    
    def run_support(self):
        if self.is_support_file():
            print("Skipping JCAlgTest Algorithm Support")
            return 0
        
        cmd_line = self.BIN
        retcode = execute_cmd(cmd_line)

        for file in os.listdir("./"):
            if "ALGSUPPORT" in file and self.card_name in file:
                dest = "results/" + self.card_name + "/" + file
                os.replace(file, dest)
                self.support_file = file
                break

        return retcode

    def parse_support(self):
        filename = "results/" + self.card_name + "/" + self.support_file

        jcsupport = JCSupport()

        with open(filename, "r") as f:
            lines = f.readlines()

        DISCARD = ["This file was generated by AlgTest utility",
                   "This is very specific feature"]

        TEST_INFO = ["Tested and provided by",
                     "Execution date",
                     "AlgTest",
                     "Used reader",
                     "Card ATR",
                     "Card name",
                     "Used protocol",
                     "JavaCard support version",
                     "Total test time"]
            
        i = 0
        while i < len(lines):
                
            line = lines[i].strip()
            i += 1

            if line == "" or ";" not in line \
               or any([d in line for d in DISCARD]):
                continue

            data = line.split(";")

            if any([line.startswith(info) for info in TEST_INFO]):
                jcsupport.test_info[data[0]] = data[1].strip()
                continue
                
            if line.startswith("JCSystem"):
                jcsupport.jcsystem[data[0]] = data[1]
                continue

            if line.startswith("CPLC"):
                jcsupport.cplc[data[0]] = data[1]
                continue

            #------------------
            result = (data[1], None)
            if len(data) >= 3 and data[2] != "":
                result = (data[1], data[2])
            jcsupport.support[data[0]] = result

        return jcsupport

    def parse_performance(self):
        pass

    def run(self):
        self.run_support()


class JCSupport(Module):
    def __init__(self, moduleid="jcsupport"):
        super().__init__(moduleid)
        self.test_info = {}
        self.jcsystem = {}
        self.cplc = {}
        self.support = {}
