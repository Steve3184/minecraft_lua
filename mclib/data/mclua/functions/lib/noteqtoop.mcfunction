execute store result storage mclua:_data data.return int 1 run data get storage mclua:_data data.args[0] 100
execute store result score temp1 _luatmp run data get storage mclua:_data data.return
execute store result storage mclua:_data data.return int 1 run data get storage mclua:_data data.args[1] 100
execute store result score temp2 _luatmp run data get storage mclua:_data data.return
execute unless score temp1 _luatmp = temp2 _luatmp run data modify storage mclua:_data data.return set value 1
execute if score temp1 _luatmp = temp2 _luatmp run data remove storage mclua:_data data.return