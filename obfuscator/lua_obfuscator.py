import base64
import re
import random
import hashlib
from .utils import random_name

class LuaObfuscator:
    def __init__(self, code: str, level="hard"):
        self.code = code
        self.level = level
        self.string_table = []

    def _generate_opaque_predicate(self):
        a = random.randint(100, 999)
        b = random.randint(100, 999)
        c = a + b
        return f"(({a} + {b}) == {c})"

    def _encode_string(self, s):
        key1 = random.randint(1, 255)
        key2 = random.randint(1, 255)
        xorred = ''.join(chr(ord(c) ^ key1 ^ key2) for c in s)
        b64 = base64.b64encode(xorred.encode()).decode()
        self.string_table.append((key1, key2, b64))
        return f"__KoalaDecrypt({len(self.string_table)-1})"

    def _build_decoder(self):
        if not self.string_table:
            return ""
        entries = [f"{{{k1}, {k2}, '{b}'}}" for k1, k2, b in self.string_table]
        table_str = ", ".join(entries)
        return f'''
local function __KoalaDecode(s)
    local c = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    s = s:gsub('[^'..c..'=]', '')
    local t = {{}}
    for i = 1, #s, 4 do
        local a,b,c,d = s:byte(i,i+3)
        a = a and c:find(string.char(a),1,true) or 0
        b = b and c:find(string.char(b),1,true) or 0
        c = c and c:find(string.char(c),1,true) or 0
        d = d and c:find(string.char(d),1,true) or 0
        t[#t+1] = string.char((a*4)+math.floor(b/16), ((b%16)*16)+math.floor(c/4), ((c%4)*64)+d)
    end
    local r = table.concat(t)
    return s:sub(-2)=='==' and r:sub(1,-3) or s:sub(-1)=='=' and r:sub(1,-2) or r
end
local function __KoalaDecrypt(idx)
    local k1, k2, b = unpack({{{table_str}}}[idx+1])
    local d = __KoalaDecode(b)
    local r = ''
    for i = 1, #d do
        r = r .. string.char(d:byte(i) ~ k1 ~ k2)
    end
    return r
end
'''

    def _flatten_control_flow(self, code):
        lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith('--')]
        if not lines:
            return code

        state_var = random_name()
        dispatcher = random_name()
        states = {}
        for i, line in enumerate(lines):
            states[i] = line

        state_entries = []
        for i, line in states.items():
            state_entries.append(f"        [{i}] = function() {line} end")

        return f'''
local {state_var} = 0
local {dispatcher} = {{
{chr(10).join(state_entries)}
}}
while {state_var} < #{dispatcher} do
    if {self._generate_opaque_predicate()} then
        {dispatcher}[{state_var}]()
    end
    {state_var} = {state_var} + 1
end
'''

    def _insert_junk_code(self, code):
        junk_templates = [
            "if {pred} then local _ = nil end",
            "for i = 1, 0 do break end",
            "local __junk = function() return end; __junk()",
            "do end",
            "local a, b = 1, 2; if a < b then end"
        ]
        lines = code.splitlines()
        new_lines = []
        for i, line in enumerate(lines):
            new_lines.append(line)
            if i > 0 and i % random.randint(2, 4) == 0:
                template = random.choice(junk_templates)
                pred = self._generate_opaque_predicate()
                new_lines.append(template.replace("{pred}", pred))
        return '\n'.join(new_lines)

    def _anti_debug_trap(self):
        trap = random_name()
        return f'''
local function {trap}()
    local t = tick()
    wait(0.0001)
    if tick() - t > 0.01 then
        while true do wait() end
    end
end
{trap}()
'''

    def _anti_tamper_stub(self):
        checksum = hashlib.md5(self.code.encode()).hexdigest()
        check_var = random_name()
        return f'''
-- Protected_by_KoalaHub
local {check_var} = "{checksum}"
if #{check_var} ~= 32 then
    for _=1,1000 do pcall(function() game:Shutdown() end); wait() end
    error("Tamper detected")
end
'''

    def _rename_vars(self, code):
        roblox_globals = {'game','workspace','script','nil','true','false','print','warn','error','require','pcall','xpcall','type','typeof','getfenv','setfenv'}
        var_map = {}

        def repl(m):
            kw, name = m.groups()
            if name in roblox_globals or name.startswith('_') or len(name) < 2 or name[0].isdigit():
                return m.group(0)
            if name not in var_map:
                var_map[name] = random_name()
            return f"{kw} {var_map[name]}"
        return re.sub(r'\b(local|function)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', repl, code)

    def obfuscate(self) -> str:
        code = self.code

        if self.level == "hard":
            code = self._rename_vars(code)
            code = self._insert_junk_code(code)
            code = self._flatten_control_flow(code)
            def encode_str(m):
                quote, content = m.groups()
                return f"{quote}{self._encode_string(content)}{quote}" if len(content) > 2 else m.group(0)
            code = re.sub(r'(["\'])(.*?)\1', encode_str, code)
        else:
            code = self._rename_vars(code)
            def encode_str(m):
                quote, content = m.groups()
                return f"{quote}{self._encode_string(content)}{quote}" if len(content) > 5 else m.group(0)
            code = re.sub(r'(["\'])(.*?)\1', encode_str, code)

        output = self._anti_tamper_stub()
        if self.level == "hard":
            output += self._anti_debug_trap()
        output += self._build_decoder()
        output += code
        return output