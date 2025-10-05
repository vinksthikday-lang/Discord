import base64
import zlib
import random
import hashlib
import inspect
from .utils import random_name

class PythonObfuscator:
    def __init__(self, code: str, level="hard"):
        self.code = code
        self.level = level

    def _generate_opaque_predicate(self):
        a = random.randint(1000, 9999)
        b = random.randint(1000, 9999)
        return f"({a} * {b} == {a * b})"

    def _custom_encrypt(self, data: bytes) -> tuple:
        key = [random.randint(1, 255) for _ in range(16)]
        encrypted = []
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        return base64.b64encode(bytes(encrypted)).decode(), key

    def _layered_obfuscation(self, code: str) -> str:
        payload = code.encode()
        compressed = zlib.compress(payload)
        encrypted_b64, key = self._custom_encrypt(compressed)
        var1, var2, var3, var4 = random_name(), random_name(), random_name(), random_name()
        key_str = "[" + ", ".join(str(k) for k in key) + "]"
        
        junk_classes = []
        for _ in range(random.randint(1, 3)):
            cls_name = random_name()
            junk_classes.append(f"class {cls_name}:\n    pass\n")
        
        junk_funcs = []
        for _ in range(random.randint(2, 4)):
            func_name = random_name()
            junk_funcs.append(f"def {func_name}():\n    return None\n")
        
        return f'''
# Protected_by_KoalaHub
{"".join(junk_classes)}
{"".join(junk_funcs)}
{var1} = "{encrypted_b64}"
{var2} = {key_str}
{var3} = []
for i, b in enumerate(base64.b64decode({var1})):
    {var3}.append(b ^ {var2}[i % len({var2})])
{var4} = zlib.decompress(bytes({var3}))
exec({var4}.decode())
'''

    def _simple_obfuscation(self, code: str) -> str:
        lines = code.splitlines()
        new_lines = []
        for line in lines:
            if line.strip().startswith(('import', 'from', 'def ', 'class ')):
                new_lines.append(line)
            elif '=' in line and not line.strip().startswith('#'):
                pred = self._generate_opaque_predicate()
                new_lines.append(f"if {pred}:\n    {line}")
            else:
                new_lines.append(line)
        return "# Obfuscated by KoalaHub (easy mode)\n" + "\n".join(new_lines)

    def _anti_debug_stub(self):
        debugger_check = random_name()
        return f'''
def {debugger_check}():
    try:
        if hasattr(sys, 'gettrace') and sys.gettrace() is not None:
            raise RuntimeError("Debugger detected")
        frame = inspect.currentframe()
        if frame.f_back and 'pdb' in str(frame.f_back):
            raise RuntimeError("PDB detected")
    except:
        __import__('os')._exit(1)
{debugger_check}()
'''

    def _anti_tamper_stub(self):
        checksum = hashlib.sha256(self.code.encode()).hexdigest()
        return f'''
# Integrity: {checksum[:16]}
if len("{checksum}") != 64:
    raise RuntimeError("Tamper detected")
'''

    def obfuscate(self) -> str:
        if self.level == "hard":
            obfuscated = self._layered_obfuscation(self.code)
            lines = obfuscated.splitlines()
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.strip() and not line.startswith('#') and not line.startswith('class') and not line.startswith('def'):
                    insert_pos = i
                    break
            lines.insert(insert_pos, self._anti_debug_stub())
            lines.insert(0, self._anti_tamper_stub())
            return "\n".join(lines)
        else:
            return self._anti_tamper_stub() + "\n" + self._simple_obfuscation(self.code)