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