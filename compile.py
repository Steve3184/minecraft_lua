import luaparser as lp
from luaparser import ast
import os
SUB_PROG_ID = 0

def openSrc(fn: str):
    with open(fn, 'r') as f:
        src = f.read()
    return src

def compileLuaBlock(ast_tree: list, outfp: str):
    global SUB_PROG_ID
    result = ""
    for line in ast_tree:
        if isinstance(line, ast.Assign):
            var_name = line.targets[0].id
            value = line.values[0]
            if isinstance(value, ast.Number): result += "data modify storage mclua:_data data.var."+var_name+" set value "+str(value.n)+"d\n"
            elif isinstance(value, ast.String): result += "data modify storage mclua:_data data.var."+var_name+' set value "'+value.s+'"\n'
            elif "Op" in value.display_name:
                result += "data modify storage mclua:_data data.args set value [0d,0d]\n"
                if isinstance(value.left, ast.Number): result += "data modify storage mclua:_data data.args[0] set value "+str(value.left.n)+"d\n"
                elif isinstance(value.left, ast.Name): result += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+value.left.id+"\n"
                else: raise ValueError("vartype not supported yet")
                if isinstance(value.right, ast.Number): result += "data modify storage mclua:_data data.args[1] set value "+str(value.right.n)+"d\n"
                elif isinstance(value.right, ast.Name): result += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+value.right.id+"\n"
                else: raise ValueError("vartype not supported yet")
                
                if isinstance(value, ast.AddOp): result += "function mclua:lib/add\n"
                elif isinstance(value, ast.SubOp): result += "function mclua:lib/sub\n"
                elif isinstance(value, ast.MultOp): result += "function mclua:lib/mul\n"
                elif isinstance(value, ast.FloatDivOp): result += "function mclua:lib/div\n"
                elif isinstance(value, ast.ModOp): result += "function mclua:lib/mod\n"
                else: raise NotImplementedError("op lib not supported yet")
                
                result += "data modify storage mclua:_data data.var."+var_name+" set from storage mclua:_data data.return\n"
            else: raise ValueError("optype not supported yet")
        elif isinstance(line, ast.Call):
            if line.func.id == "print":
                if isinstance(line.args[0], ast.String):
                    result += 'tellraw @a [{"text":"'+line.args[0].s+'"}]\n'
                elif isinstance(line.args[0], ast.Number):
                    result += 'tellraw @a [{"text":"'+str(line.args[0].n)+'"}]\n'
                elif isinstance(line.args[0], ast.Name):
                    result += 'tellraw @a [{"type":"nbt","nbt":"data.var.'+line.args[0].id+'","source":"storage","storage":"mclua:_data"}]\n'
                else: raise ValueError("type not supported yet")
            elif line.func.id == "command":
                if isinstance(line.args[0], ast.String):
                    result += line.args[0].s+"\n"
                elif isinstance(line.args[0], ast.Name):
                    result += "data modify storage mclua:_data data.exec.cmd set from storage mclua:_data data.var."+line.args[0].id+"\n"
                    result += "function mclua:lib/execute with storage mclua:_data data.exec\n"
                else: raise ValueError("type not supported yet")
        elif isinstance(line, ast.If):
            result += "data modify storage mclua:_data data.args set value [0d,0d]\n"
            if isinstance(line.test.left, ast.Number): result += "data modify storage mclua:_data data.args[0] set value "+str(line.test.left.n)+"d\n"
            elif isinstance(line.test.left, ast.Name): result += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+line.test.left.id+"\n"
            else: raise ValueError("vartype not supported yet")
            if isinstance(line.test.right, ast.Number): result += "data modify storage mclua:_data data.args[1] set value "+str(line.test.right.n)+"d\n"
            elif isinstance(line.test.right, ast.Name): result += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+line.test.right.id+"\n"
            else: raise ValueError("vartype not supported yet")
            
            if isinstance(line.test, ast.EqToOp): result += "function mclua:lib/eqtoop\n"
            elif isinstance(line.test, ast.NotEqToOp): result += "function mclua:lib/noteqtoop\n"
            elif isinstance(line.test, ast.GreaterThanOp): result += "function mclua:lib/gtop\n"
            elif isinstance(line.test, ast.LessThanOp): result += "function mclua:lib/ltop\n"
            elif isinstance(line.test, ast.GreaterOrEqThanOp): result += "function mclua:lib/gteqop\n"
            elif isinstance(line.test, ast.LessOrEqThanOp): result += "function mclua:lib/lteqop\n"
            else: raise NotImplementedError("test op lib not supported yet")
            
            ifBody = compileLuaBlock(line.body.body, outfp)
            ifProgName = "sub"+str(SUB_PROG_ID)
            SUB_PROG_ID += 1
            result += "execute if data storage mclua:_data data.return run function out:"+ifProgName+"\n"
            with open(os.path.join(outfp,ifProgName+".mcfunction"),"w",encoding="utf-8") as f:
                f.write(ifBody)
            if line.orelse:
                elseBody = compileLuaBlock(line.orelse.body, outfp)
                elseProgName = "sub"+str(SUB_PROG_ID)
                SUB_PROG_ID += 1
                result += "execute unless data storage mclua:_data data.return run function out:"+elseProgName+"\n"
                with open(os.path.join(outfp,elseProgName+".mcfunction"),"w",encoding="utf-8") as f:
                    f.write(elseBody)
        elif isinstance(line, ast.While):
            whileBody = "data modify storage mclua:_data data.args set value [0d,0d]\n"
            if isinstance(line.test.left, ast.Number): whileBody += "data modify storage mclua:_data data.args[0] set value "+str(line.test.left.n)+"d\n"
            elif isinstance(line.test.left, ast.Name): whileBody += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+line.test.left.id+"\n"
            else: raise ValueError("vartype not supported yet")
            if isinstance(line.test.right, ast.Number): whileBody += "data modify storage mclua:_data data.args[1] set value "+str(line.test.right.n)+"d\n"
            elif isinstance(line.test.right, ast.Name): whileBody += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+line.test.right.id+"\n"
            else: raise ValueError("vartype not supported yet")
            
            if isinstance(line.test, ast.EqToOp): whileBody += "function mclua:lib/eqtoop\n"
            elif isinstance(line.test, ast.NotEqToOp): whileBody += "function mclua:lib/noteqtoop\n"
            elif isinstance(line.test, ast.GreaterThanOp): whileBody += "function mclua:lib/gtop\n"
            elif isinstance(line.test, ast.LessThanOp): whileBody += "function mclua:lib/ltop\n"
            elif isinstance(line.test, ast.GreaterOrEqThanOp): whileBody += "function mclua:lib/gteqop\n"
            elif isinstance(line.test, ast.LessOrEqThanOp): whileBody += "function mclua:lib/lteqop\n"
            else: raise NotImplementedError("test op lib not supported yet")
            whileBody += "execute unless data storage mclua:_data data.return run return 0\n"
            whileBody += compileLuaBlock(line.body.body, outfp)
            whileProgName = "sub"+str(SUB_PROG_ID)
            SUB_PROG_ID += 1
            whileBody += "function out:"+whileProgName+"\n"
            result += "function out:"+whileProgName+"\n"
            with open(os.path.join(outfp,whileProgName+".mcfunction"),"w",encoding="utf-8") as f:
                f.write(whileBody)
        elif isinstance(line, ast.Repeat):
            whileBody = compileLuaBlock(line.body.body, outfp)
            whileBody += "data modify storage mclua:_data data.args set value [0d,0d]\n"
            if isinstance(line.test.left, ast.Number): whileBody += "data modify storage mclua:_data data.args[0] set value "+str(line.test.left.n)+"d\n"
            elif isinstance(line.test.left, ast.Name): whileBody += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+line.test.left.id+"\n"
            else: raise ValueError("vartype not supported yet")
            if isinstance(line.test.right, ast.Number): whileBody += "data modify storage mclua:_data data.args[1] set value "+str(line.test.right.n)+"d\n"
            elif isinstance(line.test.right, ast.Name): whileBody += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+line.test.right.id+"\n"
            else: raise ValueError("vartype not supported yet")
            
            if isinstance(line.test, ast.EqToOp): whileBody += "function mclua:lib/eqtoop\n"
            elif isinstance(line.test, ast.NotEqToOp): whileBody += "function mclua:lib/noteqtoop\n"
            elif isinstance(line.test, ast.GreaterThanOp): whileBody += "function mclua:lib/gtop\n"
            elif isinstance(line.test, ast.LessThanOp): whileBody += "function mclua:lib/ltop\n"
            elif isinstance(line.test, ast.GreaterOrEqThanOp): whileBody += "function mclua:lib/gteqop\n"
            elif isinstance(line.test, ast.LessOrEqThanOp): whileBody += "function mclua:lib/lteqop\n"
            else: raise NotImplementedError("test op lib not supported yet")
            whileBody += "execute if data storage mclua:_data data.return run return 0\n"
            whileProgName = "sub"+str(SUB_PROG_ID)
            SUB_PROG_ID += 1
            whileBody += "function out:"+whileProgName+"\n"
            result += "function out:"+whileProgName+"\n"
            with open(os.path.join(outfp,whileProgName+".mcfunction"),"w",encoding="utf-8") as f:
                f.write(whileBody)
        elif isinstance(line, ast.Fornum):
            whileBody = "data modify storage mclua:_data data.args set value [0d,0d]\n"
            var_name = line.target.id
            value = line.start.n
            if isinstance(value, ast.Number): result += "data modify storage mclua:_data data.var."+var_name+" set value "+str(value.n)+"d\n"
            elif isinstance(value, ast.String): result += "data modify storage mclua:_data data.var."+var_name+' set value "'+value.s+'"\n'
            elif "Op" in value.display_name:
                result += "data modify storage mclua:_data data.args set value [0d,0d]\n"
                if isinstance(value.left, ast.Number): result += "data modify storage mclua:_data data.args[0] set value "+str(value.left.n)+"d\n"
                elif isinstance(value.left, ast.Name): result += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+value.left.id+"\n"
                else: raise ValueError("vartype not supported yet")
                if isinstance(value.right, ast.Number): result += "data modify storage mclua:_data data.args[1] set value "+str(value.right.n)+"d\n"
                elif isinstance(value.right, ast.Name): result += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+value.right.id+"\n"
                else: raise ValueError("vartype not supported yet")
                
                if isinstance(value, ast.AddOp): result += "function mclua:lib/add\n"
                elif isinstance(value, ast.SubOp): result += "function mclua:lib/sub\n"
                elif isinstance(value, ast.MultOp): result += "function mclua:lib/mul\n"
                elif isinstance(value, ast.FloatDivOp): result += "function mclua:lib/div\n"
                elif isinstance(value, ast.ModOp): result += "function mclua:lib/mod\n"
                else: raise NotImplementedError("op lib not supported yet")
                
                result += "data modify storage mclua:_data data.var."+var_name+" set from storage mclua:_data data.return\n"
            else: raise ValueError("optype not supported yet")
            
            
            
            if isinstance(line.test.left, ast.Number): whileBody += "data modify storage mclua:_data data.args[0] set value "+str(line.test.left.n)+"d\n"
            elif isinstance(line.test.left, ast.Name): whileBody += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+line.test.left.id+"\n"
            else: raise ValueError("vartype not supported yet")
            if isinstance(line.test.right, ast.Number): whileBody += "data modify storage mclua:_data data.args[1] set value "+str(line.test.right.n)+"d\n"
            elif isinstance(line.test.right, ast.Name): whileBody += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+line.test.right.id+"\n"
            else: raise ValueError("vartype not supported yet")
            
            if isinstance(line.test, ast.EqToOp): whileBody += "function mclua:lib/eqtoop\n"
            elif isinstance(line.test, ast.NotEqToOp): whileBody += "function mclua:lib/noteqtoop\n"
            elif isinstance(line.test, ast.GreaterThanOp): whileBody += "function mclua:lib/gtop\n"
            elif isinstance(line.test, ast.LessThanOp): whileBody += "function mclua:lib/ltop\n"
            elif isinstance(line.test, ast.GreaterOrEqThanOp): whileBody += "function mclua:lib/gteqop\n"
            elif isinstance(line.test, ast.LessOrEqThanOp): whileBody += "function mclua:lib/lteqop\n"
            else: raise NotImplementedError("test op lib not supported yet")
            whileBody += "execute unless data storage mclua:_data data.return run return 0\n"
            whileBody += compileLuaBlock(line.body.body, outfp)
            whileProgName = "sub"+str(SUB_PROG_ID)
            SUB_PROG_ID += 1
            whileBody += "function out:"+whileProgName+"\n"
            result += "function out:"+whileProgName+"\n"
            with open(os.path.join(outfp,whileProgName+".mcfunction"),"w",encoding="utf-8") as f:
                f.write(whileBody)
        elif isinstance(line, ast.Forin): raise NotImplementedError("for in repeat not supported in minecraft")
        else: raise NotImplementedError("not supported yet")
    return result

def compileLua(fn: str,ofp: str):
    src = openSrc(fn)
    ast_tree = ast.parse(src)
    # temp hack
    ast_tree = ast_tree.body.body
    if not os.path.exists(ofp): os.mkdir(ofp)
    with open(os.path.join(ofp,"main.mcfunction"),"w",encoding="utf-8") as f:
        m = compileLuaBlock(ast_tree, ofp)
        f.write(m)
compileLua("test.lua","/home/ubuntu/.local/share/atlauncher/instances/DCraftPack/saves/world123/datapacks/a/data/out/function")