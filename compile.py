import luaparser as lp
from luaparser import ast
import os, sys
SUB_PROG_ID = 0
var_type = {}

func_need_args = {}

def check_if_def(var_name: str, var_type):
    if var_name in var_type:
        return
    else:
        raise ValueError("var not defined: %s" % var_name)

def openSrc(fn: str):
    with open(fn, 'r') as f:
        src = f.read()
    return src

def parse_func_call(line: ast.Call, func_var_type: dict, var_area: str):
    global func_need_args
    result = ""
    ret_type = "none"
    if line.func.id == "print":
        if isinstance(line.args[0], ast.String):
            result += 'tellraw @a [{"text":"'+line.args[0].s+'"}]\n'
        elif isinstance(line.args[0], ast.Number):
            result += 'tellraw @a [{"text":"'+str(line.args[0].n)+'"}]\n'
        elif isinstance(line.args[0], ast.Name):
            check_if_def(line.args[0].id,func_var_type)
            result += 'tellraw @a [{"type":"nbt","nbt":"data.var.'+var_area+"."+line.args[0].id+'","source":"storage","storage":"mclua:_data"}]\n'
        else: raise ValueError("type not supported yet")
    elif line.func.id == "command":
        if isinstance(line.args[0], ast.String):
            result += line.args[0].s+"\n"
        elif isinstance(line.args[0], ast.Name):
            check_if_def(line.args[0].id,func_var_type)
            if func_var_type[line.args[0].id] == "string":
                result += "data modify storage mclua:_data data.exec.cmd set from storage mclua:_data data.var."+var_area+"."+line.args[0].id+"\n"
                result += "function mclua:lib/execute with storage mclua:_data data.exec\n"
            else:
                raise ValueError("wrong var types when command call (eg. number)")
        else: raise ValueError("type not supported yet")
    elif line.func.id == "str":
        if isinstance(line.args[0], ast.Name):
            check_if_def(line.args[0].id,func_var_type)
            if func_var_type[line.args[0].id] == "number":
                result += f'data modify storage mclua:_data data.return set string storage mclua:_data data.var.{var_area}.{line.args[0].id} 0 -1\n'
            else:
                result += f'data modify storage mclua:_data data.return set string storage mclua:_data data.var.{var_area}.{line.args[0].id}\n'
        elif isinstance(line.args[0], ast.String):
            result += f"data modify storage mclua:_data data.return set value '{str(line.args[0].s)}'\n"
        elif isinstance(line.args[0], ast.Number):
            result += f"data modify storage mclua:_data data.return set value '{str(line.args[0].n)}'\n"
        else: raise ValueError("type not supported yet")
        ret_type = "string"
    elif line.func.id in func_need_args:
        func_name = line.func.id
        if not len(line.args) == len(func_need_args[func_name]): raise ValueError("func call arg wrong")
        i = 0
        for arg in line.args:
            if isinstance(arg, ast.Number):
                result += "data modify storage mclua:_data data.var."+func_name+"."+str(func_need_args[func_name][i]["name"])+" set value "+str(arg.n)+"d\n"
            elif isinstance(arg, ast.String):
                result += "data modify storage mclua:_data data.var."+func_name+"."+str(func_need_args[func_name][i]["name"])+" set value "+str(arg.s)+"\n"
            elif isinstance(arg, ast.Name):
                if not func_need_args[func_name][i]["type"] == func_var_type[arg.id]: raise ValueError("Type mismatch")
                result += "data modify storage mclua:_data data.var."+func_name+"."+str(func_need_args[func_name][i]["name"])+" set from storage mclua:_data data.var."+var_area+"."+arg.id+"\n"
            else: raise ValueError("type on arg call not supported yet")
            i += 1
        result += "function out:"+func_name+"\n"
    return result,ret_type

def compileLuaBlock(ast_tree: list, outfp: str, sub_vartype={}, var_area="global"):
    global SUB_PROG_ID,func_need_args
    global var_type
    func_var_type = {**var_type, **sub_vartype}
    result = ""
    for line in ast_tree:
        if isinstance(line, ast.Assign):
            var_name = line.targets[0].id
            value = line.values[0]
            if isinstance(value, ast.Number):
                func_var_type[var_name] = "number"
                result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set value "+str(value.n)+"d\n"
            elif isinstance(value, ast.String):
                func_var_type[var_name] = "string"
                result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+' set value "'+value.s+'"\n'
            elif "Op" in value.display_name and not (isinstance(value.left, ast.String) and isinstance(value.right, ast.String)):
                str_op = False
                if isinstance(value.left, ast.Number):
                    result += "data modify storage mclua:_data data.args set value [0d,0d]\n"
                    result += "data modify storage mclua:_data data.args[0] set value "+str(value.left.n)+"d\n"
                elif isinstance(value.left, ast.Name):
                    check_if_def(value.left.id,func_var_type)
                    if func_var_type[value.left.id] == "number":
                        result += "data modify storage mclua:_data data.args set value [0d,0d]\n"
                        result += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+value.left.id+"\n"
                    elif func_var_type[value.left.id] == "string":
                        result += "data modify storage mclua:_data data.args set value {a:'',b:''}\n"
                        result += "data modify storage mclua:_data data.args.a set from storage mclua:_data data.var."+value.left.id+"\n"
                elif isinstance(value.left, ast.String):
                    result += "data modify storage mclua:_data data.args set value {a:'"+value.left.s+"',b:''}\n"
                else: raise ValueError("vartype not supported yet")
                if isinstance(value.right, ast.Number):
                    func_var_type[var_name] = "number"
                    result += "data modify storage mclua:_data data.args[1] set value "+str(value.right.n)+"d\n"
                elif isinstance(value.right, ast.Name):
                    check_if_def(value.right.id,func_var_type)
                    if func_var_type[value.right.id] == "number":
                        result += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+var_area+"."+value.right.id+"\n"
                        func_var_type[var_name] = "number"
                    elif isinstance(value.left, ast.String) and func_var_type[value.right.id] == "string":
                        result += "data modify storage mclua:_data data.args.b set from storage mclua:_data data.var."+var_area+"."+value.right.id+"\n"
                        str_op = True
                        func_var_type[var_name] = "string"
                    elif func_var_type[value.left.id] == "string" and func_var_type[value.right.id] == "string":
                        result += "data modify storage mclua:_data data.args.b set from storage mclua:_data data.var."+var_area+"."+value.right.id+"\n"
                        str_op = True
                        func_var_type[var_name] = "string"
                    else:
                        raise ValueError("wrong var types (eg. number + string)")
                elif isinstance(value.right, ast.String):
                    result += "data modify storage mclua:_data data.args.b set value '"+value.right.s+"'\n"
                    str_op = True
                    func_var_type[var_name] = "string"
                else: raise ValueError("vartype not supported yet")
                if isinstance(value, ast.AddOp) and str_op: result += "function mclua:lib/combine_str with storage mclua:_data data.args\n"
                elif isinstance(value, ast.AddOp): result += "function mclua:lib/add\n"
                elif isinstance(value, ast.SubOp): result += "function mclua:lib/sub\n"
                elif isinstance(value, ast.MultOp): result += "function mclua:lib/mul\n"
                elif isinstance(value, ast.FloatDivOp): result += "function mclua:lib/div\n"
                elif isinstance(value, ast.ModOp): result += "function mclua:lib/mod\n"
                else: raise NotImplementedError("op lib not supported yet")
                
                result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set from storage mclua:_data data.return\n"
            elif "Op" in value.display_name and isinstance(value.left, ast.String) and isinstance(value.right, ast.String):
                result += 'function mclua:lib/combine_str {a:"'+value.left.s+'",b:"'+value.right.s+'"}'
                result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set from storage mclua:_data data.return\n"
            elif isinstance(value, ast.Call):
                call_block,ret_type = parse_func_call(value,func_var_type,var_area)
                result += call_block
                if ret_type != 'none':
                    func_var_type[var_name] = ret_type
                    result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set from storage mclua:_data data.return\n"
                else:
                    func_var_type[var_name] = "number"
                    result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set value 0d\n"
            elif isinstance(value, ast.Name):
                result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set from storage mclua:_data data.var."+var_area+"."+value.id+"\n"
            else: raise ValueError("optype not supported yet")
        elif isinstance(line, ast.Call):
            call_block,_ = parse_func_call(line,func_var_type,var_area)
            result += call_block
        elif isinstance(line, ast.If):
            result += "data modify storage mclua:_data data.args set value [0d,0d]\n"
            if isinstance(line.test.left, ast.Number): result += "data modify storage mclua:_data data.args[0] set value "+str(line.test.left.n)+"d\n"
            elif isinstance(line.test.left, ast.Name): result += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+var_area+"."+line.test.left.id+"\n"
            else: raise ValueError("vartype not supported yet")
            if isinstance(line.test.right, ast.Number): result += "data modify storage mclua:_data data.args[1] set value "+str(line.test.right.n)+"d\n"
            elif isinstance(line.test.right, ast.Name): result += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+var_area+"."+line.test.right.id+"\n"
            else: raise ValueError("vartype not supported yet")
            
            if isinstance(line.test, ast.EqToOp): result += "function mclua:lib/eqtoop\n"
            elif isinstance(line.test, ast.NotEqToOp): result += "function mclua:lib/noteqtoop\n"
            elif isinstance(line.test, ast.GreaterThanOp): result += "function mclua:lib/gtop\n"
            elif isinstance(line.test, ast.LessThanOp): result += "function mclua:lib/ltop\n"
            elif isinstance(line.test, ast.GreaterOrEqThanOp): result += "function mclua:lib/gteqop\n"
            elif isinstance(line.test, ast.LessOrEqThanOp): result += "function mclua:lib/lteqop\n"
            else: raise NotImplementedError("test op lib not supported yet")
            
            ifBody = compileLuaBlock(line.body.body, outfp,func_var_type,var_area)
            ifProgName = "sub"+str(SUB_PROG_ID)
            SUB_PROG_ID += 1
            result += "execute if data storage mclua:_data data.return run function out:"+ifProgName+"\n"
            with open(os.path.join(outfp,ifProgName+".mcfunction"),"w",encoding="utf-8") as f:
                f.write(ifBody)
            if line.orelse:
                elseBody = compileLuaBlock(line.orelse.body, outfp,func_var_type,var_area)
                elseProgName = "sub"+str(SUB_PROG_ID)
                SUB_PROG_ID += 1
                result += "execute unless data storage mclua:_data data.return run function out:"+elseProgName+"\n"
                with open(os.path.join(outfp,elseProgName+".mcfunction"),"w",encoding="utf-8") as f:
                    f.write(elseBody)
        elif isinstance(line, ast.While):
            whileBody = "data modify storage mclua:_data data.args set value [0d,0d]\n"
            if isinstance(line.test.left, ast.Number): whileBody += "data modify storage mclua:_data data.args[0] set value "+str(line.test.left.n)+"d\n"
            elif isinstance(line.test.left, ast.Name): whileBody += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+var_area+"."+line.test.left.id+"\n"
            else: raise ValueError("vartype not supported yet")
            if isinstance(line.test.right, ast.Number): whileBody += "data modify storage mclua:_data data.args[1] set value "+str(line.test.right.n)+"d\n"
            elif isinstance(line.test.right, ast.Name): whileBody += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+var_area+"."+line.test.right.id+"\n"
            else: raise ValueError("vartype not supported yet")
            
            if isinstance(line.test, ast.EqToOp): whileBody += "function mclua:lib/eqtoop\n"
            elif isinstance(line.test, ast.NotEqToOp): whileBody += "function mclua:lib/noteqtoop\n"
            elif isinstance(line.test, ast.GreaterThanOp): whileBody += "function mclua:lib/gtop\n"
            elif isinstance(line.test, ast.LessThanOp): whileBody += "function mclua:lib/ltop\n"
            elif isinstance(line.test, ast.GreaterOrEqThanOp): whileBody += "function mclua:lib/gteqop\n"
            elif isinstance(line.test, ast.LessOrEqThanOp): whileBody += "function mclua:lib/lteqop\n"
            else: raise NotImplementedError("test op lib not supported yet")
            whileBody += "execute unless data storage mclua:_data data.return run return 0\n"
            whileBody += compileLuaBlock(line.body.body, outfp,func_var_type,var_area)
            whileProgName = "sub"+str(SUB_PROG_ID)
            SUB_PROG_ID += 1
            whileBody += "function out:"+whileProgName+"\n"
            result += "function out:"+whileProgName+"\n"
            with open(os.path.join(outfp,whileProgName+".mcfunction"),"w",encoding="utf-8") as f:
                f.write(whileBody)
        elif isinstance(line, ast.Repeat):
            whileBody = compileLuaBlock(line.body.body, outfp,func_var_type,var_area)
            whileBody += "data modify storage mclua:_data data.args set value [0d,0d]\n"
            if isinstance(line.test.left, ast.Number): whileBody += "data modify storage mclua:_data data.args[0] set value "+str(line.test.left.n)+"d\n"
            elif isinstance(line.test.left, ast.Name): whileBody += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+var_area+"."+line.test.left.id+"\n"
            else: raise ValueError("vartype not supported yet")
            if isinstance(line.test.right, ast.Number): whileBody += "data modify storage mclua:_data data.args[1] set value "+str(line.test.right.n)+"d\n"
            elif isinstance(line.test.right, ast.Name): whileBody += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+var_area+"."+line.test.right.id+"\n"
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
            forBody = "data modify storage mclua:_data data.args set value [0d,0d]\n"
            var_name = line.target.id
            value = line.start
            if isinstance(value, ast.Number):
                func_var_type[var_name] = "number"
                result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set value "+str(value.n)+"d\n"
            elif isinstance(value, ast.String):
                func_var_type[var_name] = "string"
                result += "data modify storage mclua:_data data.var."+var_area+"."+var_name+' set value "'+value.s+'"\n'
            else: raise ValueError("op in for define not supported yet")
            forBody += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+var_area+"."+line.target.id+"\n"
            if isinstance(line.stop, ast.Number): forBody += "data modify storage mclua:_data data.args[1] set value "+str(line.stop.n)+"d\n"
            elif isinstance(line.stop, ast.Name): forBody += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+var_area+"."+line.stop.id+"\n"
            else: raise ValueError("vartype not supported yet")
            forBody += "function mclua:lib/gtop\n"
            forBody += "execute if data storage mclua:_data data.return run data remove storage mclua:_data data.var."+var_area+"."+var_name+"\n"
            forBody += "execute if data storage mclua:_data data.return run return 0\n"
            forBody += compileLuaBlock(line.body.body, outfp,func_var_type,var_area)
            forBody += "data modify storage mclua:_data data.args set value [0d,0d]\n"
            forBody += "data modify storage mclua:_data data.args[0] set from storage mclua:_data data.var."+var_area+"."+var_name+"\n"
            if isinstance(line.step, ast.Number): forBody += "data modify storage mclua:_data data.args[1] set value "+str(line.step.n)+"d\n"
            elif isinstance(line.step, ast.Name): forBody += "data modify storage mclua:_data data.args[1] set from storage mclua:_data data.var."+var_area+"."+line.step.id+"\n"
            else: raise ValueError("vartype not supported yet")
            forBody += "function mclua:lib/add\n"
            forBody += "data modify storage mclua:_data data.var."+var_area+"."+var_name+" set from storage mclua:_data data.return\n"
            forProgName = "sub"+str(SUB_PROG_ID)
            SUB_PROG_ID += 1
            forBody += "function out:"+forProgName+"\n"
            result += "function out:"+forProgName+"\n"
            with open(os.path.join(outfp,forProgName+".mcfunction"),"w",encoding="utf-8") as f:
                f.write(forBody)
        elif isinstance(line, ast.Forin): raise NotImplementedError("for in repeat not supported in minecraft")
        elif isinstance(line, ast.Return):
            value = line.values[0]
            if isinstance(value, ast.Number): result += "data modify storage mclua:_data data.return set value "+str(value.n)+"d\n"
            elif isinstance(value, ast.String): result += 'data modify storage mclua:_data data.return set value "'+value.s+'"\n'
            elif isinstance(value, ast.Name):
                check_if_def(value.id, func_var_type)
                result += "data modify storage mclua:_data data.return set from storage mclua:_data data.var."+var_area+"."+value.id+"\n"
            else: raise ValueError("return arg type not supported yet")
        elif isinstance(line, ast.Function):
            sub_args = {}
            func_need_args[line.name.id] = []
            for arg in line.args:
                arg_type = arg.id.split("__")[-1]
                sub_args["__".join(arg.id.split("__")[:-1])] = arg_type
                func_need_args[line.name.id].append({"name":"__".join(arg.id.split("__")[:-1]),"type":arg_type})
            funcBody = compileLuaBlock(line.body.body,outfp,sub_args,line.name.id)
            funcPath = os.path.join(outfp,line.name.id+".mcfunction")
            if os.path.exists(funcPath): raise Warning("func already defined at: %s"%funcPath)
            with open(funcPath,"w",encoding="utf-8") as f:
                f.write(funcBody)
        else: raise NotImplementedError("not supported yet")
    return result

def compileLua(fn: str,ofp: str):
    src = openSrc(fn)
    ast_tree = ast.parse(src)
    ast_tree = ast_tree.body.body
    if not os.path.exists(ofp): os.mkdir(ofp)
    with open(os.path.join(ofp,"main.mcfunction"),"w",encoding="utf-8") as f:
        m = compileLuaBlock(ast_tree, ofp)
        f.write(m)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: %s <luafile> <output_folder>"%(sys.argv[0]))
        sys.exit(1)
    compileLua(sys.argv[1], sys.argv[2])
    print("Lua script compiled successfully to %s"%sys.argv[2])