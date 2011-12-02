"""
0 (White)
1 (Brown)
2 (Red)
3 (Orange)
4 (Yellow)
5 (Green)
6 (Blue)
7 (Violet)
8 (Gray)
9 (Black)

Three stacks. One begins as instructions, second as recycling, third as data. But there are instructions to change their roles.

A conveyor belt that can only hold one shirt in each position (no longer an infinite stream of stacks). It starts pre-loaded with an infinite amount of white shirts at one side, and the other side ends with a box that we're supposed to fill with a certain pattern of shirts. So (from the initial position) moving back gives us an empty cell, moving forward gives us a white shirt and sends the shirt that was on the belt (if any) to output.

There are ten instructions:

rot   Rotate all three stacks (data becomes instruction), nop and mdr switch roles
sw   Switch between recycling stack and data stack, nop and mdr switch roles
cf    Move conveyor belt forward
cb   Move conveyor belt back
+    Color top shirt in data stack to (its color + color of shirt beneath it) (for white shirts, this is simply "copy color of shirt beneath")
*     Color top shirt in data stack to (its color * color of shirt beneath it)
md  Move shirt between data stack and conveyor
mi   Move shirt between instruction stack and conveyor
mdr Move shirt from data to recycle
nop Nop


in data:

nop
nop
nop
nop
nop
nop
nop
nop
nop
md
nop
sw

in instruction:

mi
blue
md
cf
md
+
cb
md
cf
md
rot
"""
import operator


White = 0
Brown = 1
Red = 2
Orange = 3
Yellow = 4
Green = 5
Blue = 6
Violet = 7
Gray = 8
Black = 9

empty = "-"


class State(object):
    def __init__(self, instructions):
        self.i = list(instructions)
        self.i.reverse()
        self.r = []
        self.d = []
        self.c = [empty]
        self.o = []
        self.mdr_flag = False
        
    def step(self):
        i = self.i.pop()
        if i == "sw":
            self.i.append(i)
        else:
            self.r.append(i)
        self.ops[i](self)
    def loop(self):
        while True:
            print self.show()
            self.step()
#            raw_input()
            print
    
    def show(self):
        return "\n".join(map(self.show_stack, ["i", "r", "d", "c", "o"])) + "\n" + str(self.mdr_flag)
    def show_stack(self, name):
        stack = getattr(self, name)
        return name + "[" + "\t".join("%s %s" %
            ("-" if x == empty else self.op_n[x], x) for x in stack) + "]"


    def rot(self):
        self.i, self.d, self.r = self.d, self.r, self.i
        self.mdr_flag = not self.mdr_flag
    def sw(self):
        self.r, self.i = self.i, self.r
#        self.mdr_flag = not self.mdr_flag

    def cf(self):
        if len(self.c) == 0:
            self.c.append(self.n_op[White])
        value = self.c.pop()
        if value != empty:
            self.o.insert(0, value)
    def cb(self):
        self.c.append(empty)

    def add(self):
        self.op(operator.add)
    def mul(self):
        self.op(operator.mul)
    def op(self, f):
        assert len(self.d) >= 2
        a = self.op_n[self.d[-1]]
        b = self.op_n[self.d[-2]]
        self.d[-1] = self.n_op[f(a, b) % 10]

    def md(self):
        self.mx(self.d)
    def mi(self):
        self.mx(self.i)
    def mx(self, x):
        if self.c:
            value = self.c.pop()
        else:
            value = self.n_op[White]
        if value == empty:
            self.c.append(x.pop())
        else:
            self.c.append(empty)
            x.append(value)
    
    def mdr(self):
        self.generic_mdr(False)
    def mdR(self):
        self.generic_mdr(True)
    def generic_mdr(self, correct_flag):
        if self.mdr_flag == correct_flag:
            self.r.append(self.d.pop())
        else:
            pass  # nop
    ops = {
        "rot": rot,
        "sw": sw,
        "cf": cf,
        "cb": cb,
        "add": add,
        "mul": mul,
        "md": md,
        "mi": mi,
        "mdr": mdr,
        "mdR": mdR
        }
    
    op_n = {
        "rot": 0,
        "sw": 1,
        "cf": 2,
        "cb": 3,
        "add": 4,
        "mul": 5,
        "md": 6,
        "mi": 7,
        "mdr": 8,
        "mdR": 9
        }
    
    n_op = dict(map(lambda (a, b): (b, a), op_n.iteritems()))


s = State([
# infinite loop
# 
# outputs a blue shirt, then restores the code back to its previous state
# and loops


# put "reloader" in data stack, will be needed after the loop body

# reloader is: sw mdR mdR mdR ...
# there's an "mdR" to move every command used by the loop to the
# now-recycle-later-instruction-stack, then an "sw" to switch the
# recycle and instruction stacks
"mi",
    "sw",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
# this one is for the Blue that needs to be restored from the conveyor where it is safekept
"mi",
    "md",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
"mi",
    "mdR",
"md",
# place a rot on top of the recycle stack, it will be helpful when we
# "sw" to return to the original state (if only I could get rid of the
# mdr after it)
"mi",
    "rot",
"md",
"mdr",


# loop body

# put blue shirt in data stack
"mi",
State.n_op[Blue],
"md",

# clone it

# get new white shirt and put in data stack
"cf",
"md",
# color the white shirt blue
"add",

# send it to output
"cb",
"md",

# store the original blue in conveyor belt
"cf",
"md",

# now execute code in data stack!
"rot"])

s.loop()
