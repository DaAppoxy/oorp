import re
import inspect
from abc import ABC

# Operand 2 Hands
OP2H = {
        '+': 'add',
        '-': 'sub',
        '/': 'div',
        '*': 'mul',
        '==': 'ceq{T}',
        '>': 'c{S}gt{T}', # S is sign of arguments
        '<': 'c{S}lt{T}', # S is sign of arguments
}

function_keywords = [
        'extern'
]

operators = list(OP2H.keys()) + [
        '=',
]

def split(txt: str) -> list[str]:
        OPPOSITS = {
                '(':')',
                '[':']',
                '{':'}'
        }
        parenth = ""
        dbq = False
        bkslsh = False
        ret = [""]
        last = ''
        for i in txt:
                if len(parenth) >= 1:
                        if i == OPPOSITS[parenth[-1]]:
                                parenth = parenth[:-1]
                        elif i in OPPOSITS:
                                parenth += i
                        ret[-1]+=i
                elif dbq:
                        if i == '\\':
                                bkslsh = True
                                ret[-1]+=i
                        elif bkslsh:
                                ret[-1]+=i
                        elif i == '"':
                                dbq = False
                                ret[-1]+=i
                                ret.append("")
                        else:
                                bkslsh = False
                                ret[-1]+=i
                elif i == ' ':
                        ret.append("")
                elif i == '"':
                        dbq = True
                        ret.append('"')
                elif i in operators and last not in operators:
                        ret.append(i)
                elif i in OPPOSITS:
                        ret.append(i)
                        parenth += i
                else:
                        ret[-1] += i
                last = i
        return [r for i in ret if (r:=i.strip())]

def split_text(txt: str, breaker: str) -> list[str]:
        OPPOSITS = { # This will be hard-coded with a switch
                '(':')',
                '[':']',
                '{':'}'
        }
        parenth = ""
        ret = [""]
        for i in txt:
                if len(parenth) >= 1:
                        if i == OPPOSITS[parenth[-1]]:
                                parenth = parenth[:-1]
                        elif i in OPPOSITS:
                                parenth += i
                        ret[-1]+=i
                        if len(parenth) == 0 and i == '}':
                                ret.append("")
                elif i == breaker:
                        ret.append("")
                elif i in OPPOSITS:
                        ret[-1]+=i
                        parenth += i
                else:
                        ret[-1] += i
        return [r for i in ret if (r:=i.strip())]

MATCH_ANY = object()

def attr_match(obj, obj_pattern, attr_name):
    if obj_pattern[attr_name] == MATCH_ANY:
        return True
    return eval(
        re.sub("(?<!\w)\.", "_self.", obj_pattern[attr_name]),
        {"_self": getattr(obj, attr_name)}
    )

class TypeSpecifier:
    def __init__(self, T: type, condition: dict = None):
        if condition is None:
            condition = {}
        self.target = T.__name__
        self.content = {
            name: MATCH_ANY
        for name, value in inspect.getmembers(T, lambda a:not(inspect.isroutine(a)))
            if not name.startswith("__")
        }
        for i in condition:
            self.content[i] = condition[i]
    def match(self, obj):
        if type(obj).__name__ != self.target:
            return False
        for attr in self.content:
            if not attr_match(obj, self.content, attr):
                return False
        return True

class Decl:
    def __init__(self, tspec: TypeSpecifier, name: str | None = None):
        self.tspec = tspec
        self.name = name
    def match(self, obj) -> bool:
        return self.tspec.match(obj)

class Syntax:
    def __init__(self, )

# Some error management bullshit
class FileDescr(ABC):
    def io_read(self):
        pass
    # def io_write(self):
    #     pass
    def path(self) -> str:
        pass
class FileDescrGetter(ABC):
    def get(self) -> FileDescr:
        pass
class PythonIO_FDG_Wrapper(FileDescrGetter):
    class WrappedFD(FileDescr):
        def __init__(self, f):
            self.f = f
        def io_read(self):
            return self.f
        def path(self):
            return self.f.name
    def __init__(self, target):
        self.target = target
    def get(self) -> FileDescr:
        return WrappedFD(self.target)
class IOStringWrapper:
    def __init__(self, content: str):
        self._c = content
    def read(self) -> str:
        return self._c
class Inline_FDG(FileDescrGetter):
    class WrappedFD(FileDescr):
        def __init__(self, content: str):
            self.io = IOStringWrapper(content)
        def io_read(self):
            raise self.io
        def path(self):
            return "<inline-code>"
    def __init__(self, content):
        self.content = content
    def get(self) -> FileDescr:
        return WrappedFD(self.content)

class Litteral:
    def __init__(self, content: str, lineno: int, fdg: FileDescrGetter):
        self.content = content
        self.lineno = lineno
        self.fdg = fdg
    def info(self, span: tuple | None):
        ret = f"""\
{self.fdg.get().path()}:{self.lineno}:
\t{self.content.strip()}"""
        if span is not None:
            begin = (
                span[0]
            -   (len(self.content) - len(self.content.strip()))
            )
            end = (
                span[1]
            -   (len(self.content) - len(self.content.strip()))
            )

            ret += (
                "\n\t"
            +   ' '*begin
            +   '^'*(end-begin)
            ) 
        return ret

class Parser:
    def __init__(self, module = object()):
        self.module = module
        if "Litteral" not in self.module.__dict__().keys():
            self.module.Litteral = Litteral
        self.syntax_tree = []
    def loads(self, oorp: str, origin: FileDescrGetter = None):
        if origin is None:
            origin = Inline_FDG(oorp)
        for line in split_text(oorp, ';'):
            cmds = split(line)
            # temporary conversion from str -> Litteral without real data
            cmds = [Litteral(cmd, 0, origin) for cmd in cmds]
            chain = []

    def loadf(self, io_or_path):
        if isinstance(io_or_path, str):
            with open(io_or_path, 'r') as f:
                return self.loadf(f)
        else:
            return self.loads(io_or_path.read(), )
    
