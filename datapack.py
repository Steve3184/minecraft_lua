"""
    A compiler that compiles lua codes to minecraft functions.
    Copyright (C) 2024 Steve3184

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import shutil
from compile import compileLua as compileLua

def make_datapack(fp,outdir,packid):
    with open(os.path.join(outdir,"pack.mcmeta"),'w',encoding="utf-8") as f:
        f.write('{"pack":{"description":"%s - MCLua 1.20.4+","pack_format":26,"supported_formats":[26,9999]}}\n'%(os.path.basename(fp)))
    if not os.path.exists(os.path.join(outdir,"data",packid,"functions")):
        os.makedirs(os.path.join(outdir,"data",packid,"functions"))
    compileLua(fp,os.path.join(outdir,"data",packid,"functions"),packid)
    shutil.copytree(os.path.join(outdir,"data",packid,"functions"),os.path.join(outdir,"data",packid,"function"))
    shutil.copytree(os.path.join(os.getcwd(),"mclib","data","mclua"),os.path.join(outdir,"data","mclua"))
    shutil.copytree(os.path.join(outdir,"data","mclua","functions"),os.path.join(outdir,"data","mclua","function"))

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: %s <luafile> <out path> <pack id>"%(sys.argv[0]))
        sys.exit(1)

    luafile = sys.argv[1]
    output_fp = sys.argv[2]
    pack_id = sys.argv[3]
    if os.path.isdir(output_fp) and not os.path.isfile(os.path.join(output_fp,"pack.mcmeta")):
        print("Directory %s already exists, please delete it first."%(output_fp))
    if not os.path.exists(output_fp):
        os.makedirs(output_fp)
    make_datapack(luafile, output_fp, pack_id)
    print("done.")