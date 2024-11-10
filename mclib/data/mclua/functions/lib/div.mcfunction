execute store result storage mclua:_data data.return int 1 run data get storage mclua:_data data.args[0] 100
execute store result score temp1 _luatmp run data get storage mclua:_data data.return
execute store result storage mclua:_data data.return int 1 run data get storage mclua:_data data.args[1] 100
execute store result score temp2 _luatmp run data get storage mclua:_data data.return
scoreboard players operation temp1 _luatmp /= temp2 _luatmp
execute store result storage mclua:_data data.return double 0.01 run scoreboard players get temp1 _luatmp
