# mclua - Lua Compiler for Minecraft Datapacks

still in development

## features

- [x] Variable defines
- [x] Function defines
- [x] Function calls
- [x] print/command functions
- [x] String combines
- [x] For in/While/Repeat
- [x] If/Else
- [ ] advanced math functions
- [ ] better performance
- [ ] variable local range
...

## examples

```lua
a = "hello world!"
function hello( arg1__string )
    aa = "func:" + arg1
    print(aa)
    return aa
end
hello(a)
c = 123 % 5
if c == 3 then
    print("right!")
else
    print("wrong!")
end
for i=0,3,1 do
    j = str(i)
    j = "Counter: " + j
    print(j)
end
print("mclua demo end")
```

## installation

on Linux/Mac OS:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 copmile.py <filename> <output path>
```

on Windows (PowerShell):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
python -m venv .venv
.venv/bin/activate.ps1
pip install -r requirements.txt

python copmile.py <filename> <output path>
```
